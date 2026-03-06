import json
import anthropic

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic()


def run_agent_loop(
    system_prompt: str,
    user_message: str,
    tools: list[dict] | None = None,
    tool_executor: callable | None = None,
) -> str:
    """
    Runs an agentic loop until the model reaches end_turn.
    Returns the final text response from the model.
    """
    messages = [{"role": "user", "content": user_message}]
    kwargs = {"model": MODEL, "max_tokens": 4096, "system": system_prompt, "messages": messages}
    if tools:
        kwargs["tools"] = tools

    while True:
        response = client.messages.create(**kwargs)

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        if response.stop_reason == "tool_use" and tool_executor:
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = tool_executor(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            kwargs["messages"] = messages
        else:
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""


def extract_json(text: str) -> dict:
    """Extract the first JSON object from a text response."""
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in response:\n{text}")
    return json.loads(text[start:end])
