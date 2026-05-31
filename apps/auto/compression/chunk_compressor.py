"""
Incremental Chunk Compressor

Compresses message chunks using global overview as context.
Implements the "Overview-Guided Chunking" strategy.
"""

import json
import logging
from typing import Optional
from langchain_core.language_models import BaseLLM

from apps.core.models.ai_models import Thread
from apps.core.models import (
    MessageCompressionChunk,
    GlobalContextOverview,
)

logger = logging.getLogger(__name__)


class IncrementalChunkCompressor:
    """
    Compresses message chunks with global overview guidance.
    
    For each chunk, combines:
    1. Global overview (high-level context)
    2. Local chunk content (specific messages)
    
    This helps the compression model understand which local details
    are strategically important to retain.
    """
    
    def __init__(self, thread: Thread, llm: BaseLLM, overview: GlobalContextOverview):
        """
        Initialize compressor.
        
        Args:
            thread: Thread being compressed
            llm: Language model for compression (recommend Haiku)
            overview: Global overview to guide compression
        """
        self.thread = thread
        self.llm = llm
        self.overview = overview
        self.logger = logger.getChild(f"thread_{thread.id}")
    
    def compress_chunk(self, chunk: MessageCompressionChunk) -> dict:
        """
        Compress a single chunk with overview guidance.
        
        Args:
            chunk: MessageCompressionChunk to compress
        
        Returns:
            Dictionary with compressed content and metadata
        """
        # Format overview context
        overview_context = self._format_overview_context()
        
        # Format chunk content
        chunk_content = self._format_chunk_content(chunk)
        
        # Create compression prompt
        prompt = self._create_compression_prompt(overview_context, chunk_content)
        
        # Call LLM for compression
        try:
            response = self.llm.invoke(prompt)
            compressed_text = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            self.logger.error(f"LLM compression error: {e}")
            compressed_text = chunk_content  # Fallback
        
        # Parse result
        result = {
            'compressed_content': self._parse_compressed_result(compressed_text),
            'original_size': len(json.dumps(chunk.original_content)),
            'compressed_size': len(compressed_text),
            'compression_ratio': 1.0 - (len(compressed_text) / len(json.dumps(chunk.original_content)))
        }
        
        self.logger.debug(
            f"Chunk {chunk.chunk_index}: {result['original_size']} → {result['compressed_size']} bytes "
            f"(ratio: {result['compression_ratio']:.1%})"
        )
        
        return result
    
    def _format_overview_context(self) -> str:
        """Format global overview for inclusion in prompt."""
        parts = [
            f"MISSION: {self.overview.mission}",
            f"PHASE: {self.overview.current_phase}",
        ]
        
        if self.overview.confirmed_vulnerabilities:
            parts.append("CONFIRMED VULNERABILITIES:")
            for vuln in self.overview.confirmed_vulnerabilities[:5]:  # Top 5
                if isinstance(vuln, dict):
                    parts.append(f"  - {vuln.get('title', 'Unknown')}")
                else:
                    parts.append(f"  - {vuln}")
        
        if self.overview.critical_artifacts:
            parts.append("CRITICAL ARTIFACTS TO PRESERVE:")
            for artifact in self.overview.critical_artifacts[:3]:
                if isinstance(artifact, dict):
                    parts.append(f"  - {artifact.get('type', 'Unknown')}: {artifact.get('location', '')}")
                else:
                    parts.append(f"  - {artifact}")
        
        return "\n".join(parts)
    
    def _format_chunk_content(self, chunk: MessageCompressionChunk) -> str:
        """Format chunk messages for compression."""
        parts = []
        
        if isinstance(chunk.original_content, list):
            for msg in chunk.original_content:
                msg_type = msg.get('type', 'unknown')
                content = msg.get('content', {})
                
                if isinstance(content, dict):
                    content_text = content.get('content', '')
                else:
                    content_text = str(content)[:500]  # Truncate
                
                if msg_type == 'human':
                    parts.append(f"[USER]: {content_text}")
                elif msg_type == 'ai':
                    parts.append(f"[AI]: {content_text}")
                elif msg_type == 'tool':
                    tool_name = msg.get('name', 'tool')
                    parts.append(f"[{tool_name}]: {content_text[:300]}")
        
        return "\n".join(parts)
    
    def _create_compression_prompt(self, overview: str, chunk: str) -> str:
        """Create compression prompt."""
        return f"""
You are an expert at compressing penetration testing conversation history.

STRATEGIC CONTEXT (use to guide compression decisions):
{overview}

MESSAGES TO COMPRESS (maintain all strategic details, remove verbosity):
{chunk}

Compress the messages by:
1. Removing redundant explanations and verbose descriptions
2. Converting long tool outputs to concise one-line summaries
3. Preserving all vulnerability discoveries and exploitation details
4. Keeping exact command parameters and configurations
5. Removing repetitive greetings and explanations

Output the compressed version directly, maintaining JSON structure if present.
Focus on reducing 40-60% of content while keeping all strategic value.
"""

    
    def _parse_compressed_result(self, result: str) -> str:
        """
        Parse LLM compression result.
        
        Args:
            result: Raw LLM output
        
        Returns:
            Cleaned compressed content
        """
        # Remove markdown code blocks if present
        if result.startswith('```'):
            result = result.split('```')[1]
            if result.startswith('json'):
                result = result[4:]
        
        return result.strip()
    
    def compress_all_chunks(self) -> dict:
        """
        Compress all chunks in the thread.
        
        Returns:
            Dictionary with compression statistics
        """
        chunks = self.thread.compression_chunks.all().order_by('chunk_index')
        
        total_original = 0
        total_compressed = 0
        successful = 0
        
        for chunk in chunks:
            try:
                result = self.compress_chunk(chunk)
                
                # Update chunk in database
                chunk.compressed_content = result['compressed_content']
                chunk.compression_ratio = result['compression_ratio']
                chunk.save(update_fields=['compressed_content', 'compression_ratio'])
                
                total_original += result['original_size']
                total_compressed += result['compressed_size']
                successful += 1
            
            except Exception as e:
                self.logger.error(f"Failed to compress chunk {chunk.chunk_index}: {e}")
                continue
        
        overall_ratio = 1.0 - (total_compressed / total_original) if total_original > 0 else 0
        
        stats = {
            'chunks_compressed': successful,
            'total_chunks': len(chunks),
            'original_bytes': total_original,
            'compressed_bytes': total_compressed,
            'overall_compression_ratio': overall_ratio,
        }
        
        self.logger.info(
            f"Compression complete: {successful}/{len(chunks)} chunks, "
            f"ratio: {overall_ratio:.1%}"
        )
        
        return stats
