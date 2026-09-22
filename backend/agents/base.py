import json
import logging
import re
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import settings

logger = logging.getLogger(__name__)

# Initialize Groq LLM
groq_api_key = settings.GROQ_API_KEY

try:
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        model_name=settings.GROQ_MODEL,
        temperature=0.0,
        groq_api_key=groq_api_key,
        model_kwargs={"response_format": {"type": "json_object"}}
    )
except Exception as e:
    logger.warning(f"Could not initialize ChatGroq ({e}). Mocking LLM for offline testing.")
    llm = None

def load_prompt(agent_name: str) -> str:
    """Load agent system prompt from text file."""
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{agent_name}.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return f"You are the {agent_name} agent. Return valid JSON."

def sanitize_code_comments(code: str) -> str:
    """Sanitize prompt injection attempts in student code comments."""
    if not code:
        return ""
    pattern = r"(?i)(ignore\s+previous|system\s+prompt|admin\s+override|give\s+100)"
    sanitized = re.sub(pattern, "[FILTERED_DIRECTIVE]", code)
    return sanitized

def extract_clean_json(text: str) -> str:
    """Extract clean JSON string, stripping thinking tags and markdown."""
    # Remove thinking tags if present
    if "<think>" in text and "</think>" in text:
        text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    
    # Strip markdown codeblocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
        
    return text.strip()

async def invoke_agent(system_prompt: str, user_payload: Dict[str, Any], schema: type[BaseModel], fallback_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke Groq LLM with strict JSON validation and fallback handling."""
    if not llm or not settings.GROQ_API_KEY:
        logger.info("Using deterministic fallback logic (No GROQ_API_KEY provided)")
        return fallback_dict

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(user_payload))
        ]
        response = await llm.ainvoke(messages)
        content = extract_clean_json(response.content)
        
        validated = schema.model_validate_json(content)
        return validated.model_dump()
    except Exception as e:
        logger.error(f"Error invoking agent with Groq: {e}. Utilizing graceful fallback.")
        return fallback_dict
