import logging
from typing import Optional, Sequence
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from apps.ai_assistant import AIAssistant, method_tool
from apps.core.llms import get_llm_instance
from apps.auto.tools.skill_creator_agent import create_skill_from_spec
from apps.core.models.analyze.SkillTemplate import SkillTemplate

logger = logging.getLogger(__name__)

SKILL_CREATOR_AGENT_INSTRUCTIONS = """<system_role>
You are SkillCreatorAgent — a highly specialized AI assistant whose ONLY job is to create
and manage SkillTemplate objects in a Django-based penetration testing platform.

Your responsibilities:
1. Analyze skill creation requests carefully
2. Use the `create_skill` tool to create new skills in the database
3. Use `search_existing_skills` to check for similar existing skills before creating new ones
4. Use `load_skill_details` to examine existing skills if needed
</system_role>

<skill_creation_contract>
When creating a skill, the platform will automatically:
  1. Generate script_body based on your task_description
  2. Validate AST syntax (for Python)
  3. Inject Pydantic I/O Contract (SkillInput / SkillOutput classes)
  4. Wrap with input validation and output emission functions
  5. Save everything to the database

Your role is to be the orchestrator: you receive the complete specification,
verify it makes sense, and call the `create_skill` tool to handle the actual
code generation and database persistence.
</skill_creation_contract>

<script_body_format_rules>
The generated script_body must follow these rules:
1. The FIRST function MUST be `def main(inputs: SkillInput) -> None:`
   (or `def main() -> None:` if no input schema)
2. You MAY define helper functions BEFORE or AFTER main()
3. You MAY import third-party libraries inside function bodies
4. Use `_emit_output({"key": value, "success": True})` to emit structured output
5. Keep the script_body focused and minimal — no boilerplate
6. DO NOT write: imports for sys/argparse/json, CLI arg parsing, print statements for output,
   sys.exit() calls, or anything that handles I/O. The platform handles all I/O.
</script_body_format_rules>

<workflow>
When you receive a skill creation request:
1. First, use `search_existing_skills` to check if a similar skill already exists
2. If similar skill exists, consider whether to improve it or create a new one
3. If creating a new one, call `create_skill` with all the provided parameters
4. Return the result to the user in a clear, friendly format
</workflow>
"""


class SkillCreatorAgent(AIAssistant):
    id = "skill_creator_agent"
    name = "Skill Creator Agent"
    instructions = SKILL_CREATOR_AGENT_INSTRUCTIONS
    temperature = 0.1

    def __init__(
        self,
        step_id: Optional[int] = None,
        thread=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.step_id = step_id
        self._thread = thread

    def get_callbacks(self) -> Sequence[BaseCallbackHandler]:
        return []

    def get_llm(self):
        return get_llm_instance(
            agent_id="skill_creator_agent",
            temperature=0.1
        )

    @method_tool
    def create_skill(
        self,
        name: str,
        description: str,
        instructions: str,
        task_description: str,
        input_schema: Optional[dict] = None,
        output_schema: Optional[dict] = None,
        language: str = "python",
        tags: Optional[list] = None,
    ) -> str:
        """
        Create a new skill in the database.
        
        Args:
            name: Unique kebab-case identifier for the skill
            description: Short description (≤ 500 chars) for RAG retrieval
            instructions: Usage guide (≤ 2000 chars)
            task_description: Natural language description of what the script should do
            input_schema: JSON schema for input parameters
            output_schema: JSON schema for expected output
            language: 'python' or 'bash'
            tags: List of tag strings
            
        Returns:
            Result message indicating success or failure
        """
        try:
            result = create_skill_from_spec(
                name=name,
                description=description,
                instructions=instructions,
                task_description=task_description,
                input_schema=input_schema,
                output_schema=output_schema,
                language=language,
                tags=tags,
                llm=self.get_llm(),
            )

            if result.get("ok"):
                action = result.get("action", "Saved")
                skill_id = result["skill_id"]
                script_body = result.get("script_body", "")
                full_len = result.get("script_content_length", 0)
                return (
                    f"✅ **Success!** {action} skill '{name}' (ID: {skill_id})\n\n"
                    f"📝 **Script Body Preview**:\n```python\n{script_body[:500]}...```\n\n"
                    f"🔧 **Assembled Script**: {full_len} chars (I/O Contract auto-injected)"
                )
            else:
                return f"❌ **Error**: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.exception(f"Failed to create skill: {e}")
            return f"❌ **Exception**: {str(e)}"

    @method_tool
    def search_existing_skills(self, query: str) -> str:
        """
        Search for existing skills in the database.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching skills
        """
        from django.db.models import Q
        skills = SkillTemplate.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        ).order_by('-is_robust', '-usage_count')[:10]
        
        if not skills.exists():
            return f"No skills found matching '{query}'."
            
        result = [f"Found {skills.count()} skill(s):"]
        for skill in skills:
            robust_badge = " [ROBUST]" if skill.is_robust else ""
            result.append(
                f"- **{skill.name}** v{skill.version}{robust_badge}\n"
                f"  Tags: {skill.tags}\n"
                f"  Usage: {skill.usage_count}\n"
                f"  Description: {skill.description}"
            )
        return "\n".join(result)

    @method_tool
    def load_skill_details(self, name: str) -> str:
        """
        Load detailed information about an existing skill.
        
        Args:
            name: Skill name
            
        Returns:
            Detailed skill information
        """
        import json
        try:
            skill = SkillTemplate.objects.get(name=name)
            msg = f"**Skill**: {skill.name} v{skill.version}\n"
            msg += f"**Tags**: {skill.tags}\n"
            msg += f"**Usage Count**: {skill.usage_count}\n"
            msg += f"**Is Robust**: {skill.is_robust}\n"
            
            if skill.input_schema:
                msg += f"\n**Input Schema**:\n```json\n{json.dumps(skill.input_schema, indent=2)}\n```\n"
            
            if skill.output_schema:
                msg += f"\n**Output Schema**:\n```json\n{json.dumps(skill.output_schema, indent=2)}\n```\n"
            
            msg += f"\n**Instructions**:\n{skill.instructions}\n"
            msg += f"\n**Script Content** ({skill.language}):\n```python\n{skill.script_content or 'No script contents.'}\n```"
            
            return msg
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' does not exist."
