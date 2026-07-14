"""
Tool Output Lifecycle Manager

Implements the three-state retention strategy for tool outputs:
1. DISCARD: Remove entirely
2. TEXTUALIZE: Convert to text summary
3. RETAIN: Keep full content
"""

import json
import logging
from typing import Literal
from langchain_core.language_models import BaseLLM

from apps.core.models.ai_models import Message
from apps.core.models import ToolOutputLifecycle

logger = logging.getLogger(__name__)


class ToolOutputLifecycleManager:
    """
    Manages the lifecycle and retention strategy for tool outputs.
    
    Strategy selection is based on:
    1. Tool type and importance
    2. Output size
    3. Content significance
    """
    
    # Configuration for tool retention strategies
    TOOL_STRATEGIES = {
        # Tools that output rarely-reused large data → usually TEXTUALIZE
        'nmap': 'TEXTUALIZE',
        'sslyze': 'TEXTUALIZE',
        'whatweb': 'TEXTUALIZE',
        'nuclei': 'TEXTUALIZE',
        
        # Tools with critical payloads/exploits → RETAIN
        'sqlmap': 'RETAIN',
        'metasploit': 'RETAIN',
        'exploit_payload': 'RETAIN',
        'credentials_found': 'RETAIN',
        
        # Tools that are temporary/cleanup → DISCARD
        'cleanup': 'DISCARD',
        'temp_test': 'DISCARD',
    }
    
    # Size thresholds (in characters)
    DISCARD_THRESHOLD = 100       # Very small, likely unimportant
    TEXTUALIZE_THRESHOLD = 5000   # Medium size, can be summarized
    RETAIN_THRESHOLD = 50000      # Very large, likely critical
    
    def __init__(self, llm: BaseLLM):
        """
        Initialize manager.
        
        Args:
            llm: Language model for summarization
        """
        self.llm = llm
        self.logger = logger
    
    def process_tool_message(self, message: Message) -> ToolOutputLifecycle:
        """
        Process a tool output message and determine retention strategy.
        
        Args:
            message: Tool result message to process
        
        Returns:
            ToolOutputLifecycle model instance
        """
        from apps.auto.compression.message_utils import extract_msg_fields

        if message.role != "tool_result" and not message.is_tool_output:
            raise ValueError(f"Message {message.id} is not a tool output")
        
        # Extract tool info (use shared helper for nested LangChain dict)
        fields = extract_msg_fields(message)
        tool_name = fields["name"] or "unknown"
        output_content = fields["content"]
        output_size = len(str(output_content))
        
        # Decide strategy
        strategy = self._decide_strategy(tool_name, output_size, output_content)
        
        # Process according to strategy
        if strategy == 'DISCARD':
            processed = None
            reason = f"Tool output size {output_size} chars - discarding non-critical output"
        
        elif strategy == 'TEXTUALIZE':
            processed = self._textualize(tool_name, output_content)
            reason = f"Large output ({output_size} chars) - converted to summary"
        
        elif strategy == 'RETAIN':
            processed = output_content
            reason = f"Critical tool output - retaining full content"
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Create lifecycle record
        lifecycle = ToolOutputLifecycle.objects.create(
            message=message,
            tool_name=tool_name,
            strategy=strategy,
            original_output_size=output_size,
            compressed_output=processed,
            compressed_size=len(str(processed)) if processed else 0,
            reason=reason
        )
        
        self.logger.info(
            f"Tool {tool_name}: {strategy} "
            f"({output_size} → {lifecycle.compressed_size} chars)"
        )
        
        return lifecycle
    
    def _decide_strategy(
        self,
        tool_name: str,
        output_size: int,
        output_content: str
    ) -> Literal['DISCARD', 'TEXTUALIZE', 'RETAIN']:
        """
        Decide retention strategy based on multiple factors.
        
        Priority: Config > Size > Default
        
        Args:
            tool_name: Name of the tool
            output_size: Size of output in characters
            output_content: Actual output content
        
        Returns:
            Strategy: DISCARD, TEXTUALIZE, or RETAIN
        """
        # 1. Check config-based rules
        if tool_name in self.TOOL_STRATEGIES:
            return self.TOOL_STRATEGIES[tool_name]
        
        # 2. Check size-based rules
        if output_size < self.DISCARD_THRESHOLD:
            return 'DISCARD'
        
        if output_size > self.RETAIN_THRESHOLD:
            return 'RETAIN'
        
        if output_size > self.TEXTUALIZE_THRESHOLD:
            return 'TEXTUALIZE'
        
        # 3. Default: TEXTUALIZE for medium outputs
        return 'TEXTUALIZE'
    
    def _textualize(self, tool_name: str, output_content: str) -> str:
        """
        Convert tool output to concise text summary.
        
        Args:
            tool_name: Name of tool
            output_content: Original output
        
        Returns:
            Text summary
        """
        # Truncate very large content first
        truncated = str(output_content)[:3000]
        
        prompt = f"""
Summarize this {tool_name} tool output in a single line (max 200 chars):

{truncated}

Summary (action-oriented, factual):
"""
        
        try:
            response = self.llm.invoke(prompt)
            summary = response.content if hasattr(response, 'content') else str(response)
            # Clean up the summary
            summary = summary.strip()
            if len(summary) > 200:
                summary = summary[:197] + "..."
            return summary
        
        except Exception as e:
            self.logger.warning(f"Error texualizing {tool_name}: {e}")
            # Fallback summary
            return f"{tool_name}: {truncated[:100]}..."
    
    def apply_lifecycle_to_message(self, message: Message) -> Message:
        """
        Apply the tool lifecycle strategy to modify the message.
        
        Only sets `compressed_content` — the original `message.message` is preserved
        per the compression contract ("Never deletes data").
        
        Args:
            message: Message to modify
        
        Returns:
            Modified message
        """
        from apps.auto.compression.message_utils import build_compressed_tool_dict

        try:
            lifecycle = message.tool_lifecycle
        except ToolOutputLifecycle.DoesNotExist:
            # First time processing - create lifecycle
            lifecycle = self.process_tool_message(message)
        
        # Apply strategy to compressed_content only (original message.message preserved)
        if lifecycle.strategy == 'DISCARD':
            message.compressed_content = build_compressed_tool_dict(
                message,
                compressed_content_str=f"[Tool output discarded - size: {lifecycle.original_output_size} chars]",
                tool_name=lifecycle.tool_name,
            )
        
        elif lifecycle.strategy == 'TEXTUALIZE':
            message.compressed_content = build_compressed_tool_dict(
                message,
                compressed_content_str=lifecycle.compressed_output or "",
                tool_name=lifecycle.tool_name,
            )
        
        elif lifecycle.strategy == 'RETAIN':
            # Keep original - no compression needed
            pass
        
        if lifecycle.strategy != 'RETAIN':
            message.compression_applied = True
        
        message.save(update_fields=['compressed_content', 'compression_applied'])
        
        return message
    
    def batch_process_tool_outputs(self, thread) -> dict:
        """
        Process all tool outputs in a thread.
        
        Args:
            thread: Thread to process
        
        Returns:
            Statistics dictionary
        """
        tool_messages = thread.messages.filter(role="tool_result")
        
        stats = {
            'total_tools': tool_messages.count(),
            'discard': 0,
            'textualize': 0,
            'retain': 0,
            'total_original_size': 0,
            'total_compressed_size': 0,
        }
        
        for msg in tool_messages:
            try:
                lifecycle = self.process_tool_message(msg)
                stats[lifecycle.strategy.lower()] += 1
                stats['total_original_size'] += lifecycle.original_output_size
                stats['total_compressed_size'] += lifecycle.compressed_size
                
                # Apply to message
                self.apply_lifecycle_to_message(msg)
            
            except Exception as e:
                self.logger.error(f"Error processing message {msg.id}: {e}")
                continue
        
        self.logger.info(
            f"Tool lifecycle processing: "
            f"DISCARD={stats['discard']}, "
            f"TEXTUALIZE={stats['textualize']}, "
            f"RETAIN={stats['retain']}"
        )
        
        return stats
