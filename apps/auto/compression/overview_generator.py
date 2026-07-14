"""
Global Context Overview Generator

Generates a high-level strategic summary of a thread's conversation
to guide compression decisions and maintain context coherence.
"""

import json
import logging
from typing import Optional, Any
from datetime import datetime

from django.db.models import F, Q
from langchain_core.language_models import BaseLLM
from langchain_core.messages import messages_from_dict

from apps.core.models.ai_models import Thread, Message
from apps.core.models import GlobalContextOverview, ThreadCompressionState

logger = logging.getLogger(__name__)


class GlobalOverviewGenerator:
    """
    Generates global context overview for a thread.
    
    This reads through all messages in a thread and produces a high-level
    summary that captures:
    - Mission/objective
    - Confirmed vulnerabilities
    - Excluded paths
    - Critical artifacts
    - Attempted exploits
    - Current phase
    - Metrics
    """
    
    def __init__(self, thread: Thread, llm: BaseLLM):
        """
        Initialize the generator.
        
        Args:
            thread: The Thread to analyze
            llm: Language model for summary generation (recommend Haiku for cost)
        """
        self.thread = thread
        self.llm = llm
        self.logger = logger.getChild(f"thread_{thread.id}")
    
    def generate(self, force: bool = False) -> GlobalContextOverview:
        """
        Generate or update the global overview.
        
        Args:
            force: Force regeneration even if recent overview exists
        
        Returns:
            GlobalContextOverview instance
        """
        # Check if we need to regenerate
        try:
            overview = self.thread.global_overview
            if not force:
                # Check if overview is recent (within 1 hour)
                from django.utils import timezone
                from datetime import timedelta
                if (timezone.now() - overview.updated_at) < timedelta(hours=1):
                    self.logger.debug(f"Using existing overview")
                    return overview
        except GlobalContextOverview.DoesNotExist:
            overview = None
        
        # Extract conversation context
        context = self._extract_context()
        
        # Generate summary via LLM
        summary = self._generate_summary(context)
        
        # Parse the summary
        parsed_summary = self._parse_summary(summary)
        
        # Update or create overview
        if overview:
            for key, value in parsed_summary.items():
                setattr(overview, key, value)
            overview.updated_at = datetime.now()
        else:
            parsed_summary['thread'] = self.thread
            overview = GlobalContextOverview.objects.create(**parsed_summary)
        
        overview.save()
        self.logger.info(f"Generated overview with {len(overview.confirmed_vulnerabilities)} vulns")
        
        return overview
    
    def _extract_context(self) -> str:
        """
        Extract all messages from thread into a readable context.
        
        Returns:
            String representation of conversation
        """
        messages = self.thread.messages.all().order_by('created_at')
        
        from apps.auto.compression.message_utils import extract_msg_fields

        context_parts = []
        for msg in messages[:100]:  # Limit to first 100 messages for efficiency
            try:
                fields = extract_msg_fields(msg)
                msg_type = fields["type"]
                content = fields["content"]
                
                if msg_type == 'human':
                    context_parts.append(f"[USER]: {content[:800]}")
                
                elif msg_type == 'ai':
                    context_parts.append(f"[AI]: {content[:800]}")
                
                elif msg_type == 'tool':
                    tool_name = fields["name"] or 'unknown'
                    context_parts.append(f"[TOOL {tool_name}]: {content[:500]}")
            
            except Exception as e:
                self.logger.warning(f"Error extracting message {msg.id}: {e}")
                continue
        
        return "\n".join(context_parts)
    
    def _generate_summary(self, context: str) -> str:
        """
        Use LLM to generate structured summary.
        
        Args:
            context: Extracted conversation context
        
        Returns:
            LLM-generated summary
        """
        prompt = f"""
Analyze this penetration testing conversation and extract:

1. MISSION: One-line objective
2. VULNERABILITIES: List of confirmed security findings (format: title|CVE|severity|location)
3. EXCLUDED_PATHS: Attack vectors that didn't work (format: path|reason)
4. ARTIFACTS: Important data found (format: type|location|importance)
5. EXPLOITS: Previous exploits attempted (format: tool|target|result)
6. PHASE: Current phase (RECONNAISSANCE|SCANNING|ENUMERATION|EXPLOITATION|POST_EXPLOITATION|CLEANUP|COMPLETED)
7. METRICS: Key metrics (hosts_discovered, ports_found, services, exploits_successful)

Conversation context:
{context[:12000]}

Output as JSON:
{{
  "mission": "...",
  "confirmed_vulnerabilities": [...],
  "excluded_paths": [...],
  "critical_artifacts": [...],
  "attempted_exploits": [...],
  "current_phase": "...",
  "metrics": {{...}}
}}
"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            self.logger.error(f"LLM error during summary generation: {e}")
            # Return default empty structure
            return json.dumps({
                "mission": self.thread.name,
                "confirmed_vulnerabilities": [],
                "excluded_paths": [],
                "critical_artifacts": [],
                "attempted_exploits": [],
                "current_phase": "RECONNAISSANCE",
                "metrics": {}
            })
    
    def _parse_summary(self, summary: str) -> dict[str, Any]:
        """
        Parse LLM output into structured fields.
        
        Args:
            summary: Raw LLM output
        
        Returns:
            Dictionary with parsed fields
        """
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', summary, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(summary)
            
            return {
                'mission': data.get('mission', self.thread.name),
                'confirmed_vulnerabilities': data.get('confirmed_vulnerabilities', []),
                'excluded_paths': data.get('excluded_paths', []),
                'critical_artifacts': data.get('critical_artifacts', []),
                'attempted_exploits': data.get('attempted_exploits', []),
                'current_phase': data.get('current_phase', 'RECONNAISSANCE'),
                'metrics': data.get('metrics', {}),
            }
        
        except Exception as e:
            self.logger.error(f"Error parsing summary: {e}")
            return {
                'mission': self.thread.name,
                'confirmed_vulnerabilities': [],
                'excluded_paths': [],
                'critical_artifacts': [],
                'attempted_exploits': [],
                'current_phase': 'RECONNAISSANCE',
                'metrics': {},
            }
