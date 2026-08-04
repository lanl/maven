from typing import Any
import json
import re
import os
from pathlib import Path

from ursa.agents.chat_agent import ChatAgent
try:
    from ursa.util.http import inject_truststore_into_ssl
except ImportError:
    raise ImportError("Ensure you have ursa-ai>=0.15.8 downloaded from pypi")
from langchain.chat_models import init_chat_model

TEMP = 0.2


def _extract_json_object(text: str) -> dict[str, Any] | None:
    if not text.strip():
        return None
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = fenced + re.findall(r"(\{.*\})", text, re.DOTALL)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def run_ursa_agent(maven_dir: str, user_prompt: str) -> dict[str, Any] | None:

    # Setup workspace and thread for conversation persistence
    workspace = Path(maven_dir) / "ursa_workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # Configure model
    inject_truststore_into_ssl()
    llm = init_chat_model(
        model=os.getenv("AI_MODEL"),
        base_url=os.getenv("AI_API_URL"),
        api_key=os.getenv("AI_API_KEY"),
        temperature=TEMP
    )

    # Create ChatAgent with conversation state
    chat_agent = ChatAgent(llm=llm, workspace=workspace, autosave_metrics=False)

    # Execute extraction with conversation maintained
    inv_chat = chat_agent.invoke(user_prompt)
    response = chat_agent.format_result(inv_chat)

    # Parse JSON response
    payload = _extract_json_object(response)

    return payload
