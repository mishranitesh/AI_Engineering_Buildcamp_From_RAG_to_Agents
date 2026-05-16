from pydantic_ai.messages import (
    ModelRequest
)


def collect_tools(messages):
    """Extract tool call names from message history."""

    tools = []

    for message in messages:
        if isinstance(message, ModelRequest):

            for part in message.parts:
                # Tool call parts have tool_name attribute
                if hasattr(part, "tool_name"):
                    tools.append(part.tool_name)

    print("tools called:", tools)
    return tools