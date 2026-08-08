from typing import Any
import json
import re

from ursa.agents.chat_agent import ChatAgent


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


def run_ursa_agent(chat_agent: ChatAgent, user_prompt: str, extract_json: bool = True) -> dict[str, Any] | str:
    """
    Run ChatAgent with conversation state.
    """
    # Execute extraction with conversation maintained
    inv_chat = chat_agent.invoke(user_prompt)
    response = chat_agent.format_result(inv_chat)

    if extract_json:
        # Parse JSON response
        return _extract_json_object(response)
    else:
        return response


# def assemble_genesis_datacard(
#     agent_output: dict[str, Any],
#     populated_markdown: str,
#     output_path: str
# ) -> None:
#     """
#     Assemble complete genesis data card with YAML front matter + populated markdown body.

#     Args:
#         agent_output: Dict with extracted metadata from agent
#         tier1_cards: Dict from get_tier1_cards() containing yaml_template and markdown_template
#         output_path: Where to write the complete data card
#     """

#     with open(output_path, 'w') as f:
#         # Write YAML front matter
#         f.write('---\n')
#         yaml.safe_dump(agent_output, f, default_flow_style=False, sort_keys=False)
#         f.write('---\n\n')
#         # Write populated markdown body
#         f.write(populated_markdown)
