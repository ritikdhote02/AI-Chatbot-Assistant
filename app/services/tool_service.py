import logging

from langchain_core.messages import ToolMessage

from app.tools.datetime_tool import get_current_datetime
from app.tools.web_search_tool import search_web

logger = logging.getLogger(__name__)


def get_available_tools():
    """
    Return all tools available to the AI assistant.
    """
    return [
        get_current_datetime,
        search_web,
    ]


def get_tool_registry():
    """
    Create a mapping between tool names and tool objects.
    """
    return {
        available_tool.name: available_tool for available_tool in get_available_tools()
    }


def execute_tool_calls(response, messages):
    """
    Execute all tool calls requested by the LLM.

    Append tool results to the conversation messages
    and return whether any tools were executed.
    """
    tool_registry = get_tool_registry()

    if not response.tool_calls:
        return False

    # Preserve the assistant's tool-call message.
    messages.append(response)

    for tool_call in response.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        logger.info(
            "Executing tool: %s with arguments: %s",
            tool_name,
            tool_args,
        )

        selected_tool = tool_registry.get(tool_name)

        if selected_tool is None:
            tool_result = f"Tool '{tool_name}' is unavailable."

        else:
            try:
                tool_result = selected_tool.invoke(tool_args)

            except Exception:
                logger.exception(
                    "Tool execution failed: %s",
                    tool_name,
                )

                tool_result = (
                    f"Tool '{tool_name}' failed during execution. "
                    "Do not invent its results."
                )

        messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"],
            )
        )

    return True


def run_tool_calling_loop(model, messages, max_iterations=4):
    """
    Run the LLM tool-calling cycle until a final answer is generated.
    """
    model_with_tools = model.bind_tools(get_available_tools())

    response = model_with_tools.invoke(messages)

    iteration = 0

    while response.tool_calls and iteration < max_iterations:

        execute_tool_calls(response, messages)

        iteration += 1

        response = model_with_tools.invoke(messages)

    if response.tool_calls:
        raise RuntimeError("Maximum tool execution iterations reached.")

    return response
