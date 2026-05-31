"""
Message Chunking Logic

Divides conversation history into logical chunks based on
THINK → ACT → RESULT cycles.
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

from apps.core.models.ai_models import Thread, Message
from apps.core.models import MessageCompressionChunk

logger = logging.getLogger(__name__)


@dataclass
class MessageChunk:
    """Represents a logical chunk of messages."""
    start_idx: int          # Index in thread messages
    end_idx: int            # Index in thread messages
    start_message_id: int   # Message DB ID
    end_message_id: int     # Message DB ID
    messages: List[Message]
    tool_calls: List[str]   # List of tool names called


class ChunkDivider:
    """
    Divides thread messages into logical chunks.
    
    Strategy: One chunk = one complete THINK → ACT → RESULT cycle
    - THINK: AI message with reasoning/planning
    - ACT: Tool call (one or more)
    - RESULT: Tool responses
    
    Until next AI message (new think cycle) = end of chunk.
    """
    
    def __init__(self, thread: Thread, chunk_size_hint: int = 50):
        """
        Initialize chunker.
        
        Args:
            thread: Thread to chunk
            chunk_size_hint: Approximate target messages per chunk
        """
        self.thread = thread
        self.chunk_size_hint = chunk_size_hint
        self.logger = logger.getChild(f"thread_{thread.id}")
    
    def divide(self, from_message_id: Optional[int] = None) -> List[MessageChunk]:
        """
        Divide thread into chunks.
        
        Args:
            from_message_id: Only chunk messages after this ID (incremental)
        
        Returns:
            List of MessageChunk objects
        """
        # Fetch messages
        query = self.thread.messages.all().order_by('id')
        if from_message_id:
            query = query.filter(id__gt=from_message_id)
        
        messages = list(query)
        
        if not messages:
            self.logger.debug("No messages to chunk")
            return []
        
        chunks = []
        current_chunk_messages = []
        current_chunk_tools = set()
        chunk_index = 0
        
        for i, msg in enumerate(messages):
            msg_data = msg.message
            msg_type = msg_data.get('type', 'unknown')
            
            current_chunk_messages.append(msg)
            
            # Track tool calls
            if msg_type == 'tool':
                tool_name = msg_data.get('name', 'unknown')
                current_chunk_tools.add(tool_name)
            
            # Determine if this is a chunk boundary
            is_chunk_end = False
            
            # Strategy 1: New AI message (after initial message) = chunk boundary
            if msg_type == 'ai' and i > 0:
                # Look back to see if there were tool calls in between
                prev_msg_type = messages[i-1].message.get('type', '')
                if prev_msg_type in ['tool', 'human']:
                    is_chunk_end = True
            
            # Strategy 2: Approximate size-based chunking
            if len(current_chunk_messages) >= self.chunk_size_hint and msg_type == 'ai':
                is_chunk_end = True
            
            # Strategy 3: Last message
            if i == len(messages) - 1:
                is_chunk_end = True
            
            # Create chunk if boundary reached
            if is_chunk_end and current_chunk_messages:
                chunk = MessageChunk(
                    start_idx=i - len(current_chunk_messages) + 1,
                    end_idx=i,
                    start_message_id=current_chunk_messages[0].id,
                    end_message_id=current_chunk_messages[-1].id,
                    messages=current_chunk_messages,
                    tool_calls=list(current_chunk_tools)
                )
                chunks.append(chunk)
                self.logger.debug(
                    f"Created chunk {chunk_index}: msgs {chunk.start_message_id}-{chunk.end_message_id}, "
                    f"tools: {chunk.tool_calls}"
                )
                chunk_index += 1
                current_chunk_messages = []
                current_chunk_tools = set()
        
        # Handle remaining messages
        if current_chunk_messages:
            chunk = MessageChunk(
                start_idx=len(messages) - len(current_chunk_messages),
                end_idx=len(messages) - 1,
                start_message_id=current_chunk_messages[0].id,
                end_message_id=current_chunk_messages[-1].id,
                messages=current_chunk_messages,
                tool_calls=list(current_chunk_tools)
            )
            chunks.append(chunk)
            self.logger.debug(
                f"Created final chunk {chunk_index}: msgs {chunk.start_message_id}-{chunk.end_message_id}"
            )
        
        self.logger.info(f"Divided thread into {len(chunks)} chunks")
        return chunks
    
    def save_chunks(self, chunks: List[MessageChunk]) -> List[MessageCompressionChunk]:
        """
        Save chunks to database.
        
        Args:
            chunks: List of MessageChunk objects
        
        Returns:
            List of saved MessageCompressionChunk models
        """
        saved_chunks = []
        
        for idx, chunk in enumerate(chunks):
            # Convert messages to JSON
            chunk_content = [
                {
                    'id': msg.id,
                    'type': msg.message.get('type'),
                    'content': msg.message,
                    'created_at': msg.created_at.isoformat()
                }
                for msg in chunk.messages
            ]
            
            try:
                db_chunk, created = MessageCompressionChunk.objects.update_or_create(
                    thread=self.thread,
                    chunk_index=idx,
                    defaults={
                        'start_message_id': chunk.start_message_id,
                        'end_message_id': chunk.end_message_id,
                        'original_content': chunk_content,
                        'tool_calls': chunk.tool_calls,
                        'compression_ratio': 0.0,  # Will be updated after compression
                    }
                )
                saved_chunks.append(db_chunk)
                self.logger.debug(f"Saved chunk {idx}")
            
            except Exception as e:
                self.logger.error(f"Error saving chunk {idx}: {e}")
                continue
        
        return saved_chunks
