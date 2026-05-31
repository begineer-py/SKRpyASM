"""
Context Compression Manager

Main orchestrator for the entire compression system.
Coordinates all components: Overview generation, chunking, compression, lifecycle.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from django.utils import timezone
from langchain_core.language_models import BaseLLM

from apps.core.models.ai_models import Thread, Message
from apps.core.models import (
    ThreadCompressionState,
    GlobalContextOverview,
)

from .overview_generator import GlobalOverviewGenerator
from .chunk_divider import ChunkDivider
from .chunk_compressor import IncrementalChunkCompressor
from .tool_lifecycle import ToolOutputLifecycleManager

logger = logging.getLogger(__name__)


class ContextCompressionManager:
    """
    Main orchestrator for context compression.
    
    Coordinates the entire compression pipeline:
    1. Global overview generation
    2. Message chunking
    3. Chunk-wise compression
    4. Tool output lifecycle management
    5. Message updates with compressed content
    
    Can run in two modes:
    - Scheduled: Periodic compression (every 50 messages or hourly)
    - Urgent: When context window approaches 128K tokens
    """
    
    # Configuration
    MESSAGES_THRESHOLD = 50        # Compress every N messages
    CONTEXT_TOKEN_THRESHOLD = 128000  # Compress when approaching this
    OVERVIEW_UPDATE_INTERVAL = timedelta(hours=1)
    
    def __init__(self, thread: Thread, llm_main: BaseLLM, llm_cheap: Optional[BaseLLM] = None):
        """
        Initialize compression manager.
        
        Args:
            thread: Thread to compress
            llm_main: Main LLM for complex tasks (Claude Opus)
            llm_cheap: Cheap LLM for simple tasks (Claude Haiku) - defaults to llm_main
        """
        self.thread = thread
        self.llm_main = llm_main
        self.llm_cheap = llm_cheap or llm_main
        self.logger = logger.getChild(f"thread_{thread.id}")
    
    def should_compress(self, force: bool = False) -> bool:
        """
        Determine if thread needs compression.
        
        Args:
            force: Force compression regardless of conditions
        
        Returns:
            True if compression is needed
        """
        if force:
            return True
        
        try:
            state = self.thread.compression_state
        except ThreadCompressionState.DoesNotExist:
            # First time - no compression needed yet
            ThreadCompressionState.objects.create(thread=self.thread)
            return False
        
        # Check if context window exceeded
        if state.requires_compression:
            return True
        
        # Check message count threshold
        current_count = self.thread.messages.count()
        if current_count - state.total_message_count >= self.MESSAGES_THRESHOLD:
            return True
        
        return False
    
    def compress(self, force: bool = False) -> dict:
        """
        Execute full compression pipeline.
        
        Args:
            force: Force compression regardless of conditions
        
        Returns:
            Dictionary with compression results
        """
        if not self.should_compress(force=force):
            self.logger.debug("Compression not needed")
            return {'skipped': True}
        
        self.logger.info("Starting compression pipeline")
        
        # Step 1: Process tool outputs with lifecycle management
        lifecycle_results = self._process_tool_lifecycle()
        
        # Step 2: Generate/update global overview
        overview = self._update_overview()
        
        # Step 3: Divide messages into chunks
        chunks = self._divide_into_chunks()
        
        # Step 4: Compress each chunk
        compression_stats = self._compress_chunks(overview, chunks)
        
        # Step 5: Update messages with compressed content
        messages_updated = self._update_message_content()
        
        # Step 6: Update compression state
        self._update_compression_state(lifecycle_results, compression_stats)
        
        results = {
            'compressed': True,
            'tool_lifecycle': lifecycle_results,
            'overview_generated': overview is not None,
            'chunks_created': len(chunks),
            'compression_stats': compression_stats,
            'messages_updated': messages_updated,
        }
        
        self.logger.info(f"Compression complete: {results}")
        return results
    
    def _process_tool_lifecycle(self) -> dict:
        """Step 1: Process tool outputs with lifecycle management."""
        self.logger.info("Processing tool output lifecycle")
        
        manager = ToolOutputLifecycleManager(self.llm_cheap)
        return manager.batch_process_tool_outputs(self.thread)
    
    def _update_overview(self) -> Optional[GlobalContextOverview]:
        """Step 2: Generate or update global overview."""
        self.logger.info("Updating global overview")
        
        try:
            generator = GlobalOverviewGenerator(self.thread, self.llm_cheap)
            overview = generator.generate()
            return overview
        except Exception as e:
            self.logger.error(f"Error generating overview: {e}")
            return None
    
    def _divide_into_chunks(self) -> list:
        """Step 3: Divide messages into logical chunks."""
        self.logger.info("Dividing messages into chunks")
        
        try:
            divider = ChunkDivider(self.thread)
            chunks = divider.divide()
            saved_chunks = divider.save_chunks(chunks)
            return saved_chunks
        except Exception as e:
            self.logger.error(f"Error chunking messages: {e}")
            return []
    
    def _compress_chunks(self, overview: Optional[GlobalContextOverview], chunks: list) -> dict:
        """Step 4: Compress each chunk with overview guidance."""
        self.logger.info(f"Compressing {len(chunks)} chunks")
        
        if not overview:
            self.logger.warning("No overview available - skipping compression")
            return {'skipped': True, 'reason': 'no_overview'}
        
        try:
            compressor = IncrementalChunkCompressor(self.thread, self.llm_main, overview)
            stats = compressor.compress_all_chunks()
            return stats
        except Exception as e:
            self.logger.error(f"Error compressing chunks: {e}")
            return {'error': str(e)}
    
    def _update_message_content(self) -> int:
        """Step 5: Update message content with compressed versions."""
        self.logger.info("Updating message content")
        
        updated_count = 0
        
        # For each chunk's compressed content, update original messages
        chunks = self.thread.compression_chunks.all()
        
        for chunk in chunks:
            if not chunk.compressed_content:
                continue
            
            try:
                # Get messages in this chunk
                messages = Message.objects.filter(
                    thread=self.thread,
                    id__gte=chunk.start_message_id,
                    id__lte=chunk.end_message_id
                )
                
                # Update each message
                for msg in messages:
                    msg.compressed_content = chunk.compressed_content
                    msg.compression_applied = True
                    msg.save(update_fields=['compressed_content', 'compression_applied'])
                    updated_count += 1
            
            except Exception as e:
                self.logger.error(f"Error updating chunk {chunk.chunk_index}: {e}")
                continue
        
        self.logger.info(f"Updated {updated_count} messages")
        return updated_count
    
    def _update_compression_state(self, lifecycle_results: dict, compression_stats: dict):
        """Step 6: Update compression state for next cycle."""
        self.logger.info("Updating compression state")
        
        try:
            state = self.thread.compression_state
        except ThreadCompressionState.DoesNotExist:
            state = ThreadCompressionState.objects.create(thread=self.thread)
        
        state.total_message_count = self.thread.messages.count()
        state.last_compressed_at = timezone.now()
        state.last_compressed_message_id = self.thread.messages.latest('id').id
        
        # Update summary
        summary = state.compression_summary or {}
        summary['last_compression'] = {
            'timestamp': state.last_compressed_at.isoformat(),
            'tool_lifecycle_results': lifecycle_results,
            'compression_stats': compression_stats,
        }
        state.compression_summary = summary
        
        # Mark as not requiring compression unless explicitly set
        state.requires_compression = False
        
        state.save()
    
    def get_messages_for_agent(self, use_compressed: bool = True, limit: Optional[int] = None) -> list:
        """
        Get messages to pass to agent.
        
        Args:
            use_compressed: Use compressed versions if available
            limit: Maximum number of recent messages to return
        
        Returns:
            List of Message objects
        """
        query = self.thread.messages.all().order_by('-created_at')
        
        if limit:
            query = query[:limit]
        
        messages = []
        for msg in query.order_by('created_at'):
            if use_compressed and msg.compression_applied and msg.compressed_content:
                # Use compressed version
                msg_obj = msg
                msg_obj.message = msg.compressed_content
                messages.append(msg_obj)
            else:
                # Use original
                messages.append(msg)
        
        return messages
    
    def get_compression_metrics(self) -> dict:
        """
        Get compression metrics for monitoring.
        
        Returns:
            Dictionary with compression statistics
        """
        try:
            state = self.thread.compression_state
        except ThreadCompressionState.DoesNotExist:
            return {'status': 'not_initialized'}
        
        chunks = self.thread.compression_chunks.all()
        
        total_original = sum((c.original_content and len(str(c.original_content))) for c in chunks)
        total_compressed = sum((c.compressed_content and len(str(c.compressed_content))) for c in chunks)
        
        return {
            'total_messages': self.thread.messages.count(),
            'last_compression': state.last_compressed_at.isoformat() if state.last_compressed_at else None,
            'chunks_count': chunks.count(),
            'original_size_bytes': total_original,
            'compressed_size_bytes': total_compressed,
            'compression_ratio': 1.0 - (total_compressed / total_original) if total_original > 0 else 0,
            'requires_compression': state.requires_compression,
        }
