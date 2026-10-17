"""A minimal tool-using agent, built directly on the Anthropic SDK: no agent framework.

The loop: call Claude, and if it asks for a tool, run the tool and send the
result back; otherwise return its text. Every Claude call and every tool call
is wrapped in a Langfuse observation, so one run is one trace with child
spans. Tracing is a no-op when Langfuse credentials are not set (tracing.py).
"""

import os
from dataclasses import dataclass, field

from tools import TOOLS, call_tool
from tracing import get_tracer

MODEL = os.environ.get("MODEL_NAME", "claude-sonnet-5")
MAX_STEPS = 5

SYSTEM_PROMPT = (
    "You are a careful assistant with two tools: calculator and count_letters. "
    "Always use them for arithmetic and for counting letters; never compute "
    "either yourself. Give a short, direct final answer once you have the result."
)


@dataclass
class AgentResult:
    answer: str
    trace_id: str
    steps: int
    messages: list = field(default_factory=list)


def _text_of(content) -> str:
    return "".join(block.text for block in content if getattr(block, "type", None) == "text")


def _usage_of(response) -> dict:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    return {
        "input": getattr(usage, "input_tokens", None),
        "output": getattr(usage, "output_tokens", None),
    }


def _dump(block):
    dump = getattr(block, "model_dump", None)
    return dump() if dump else str(block)


def run_agent(question: str, client=None, max_steps: int = MAX_STEPS) -> AgentResult:
    if client is None:
        from anthropic import Anthropic

        client = Anthropic()

    tracer = get_tracer()
    messages = [{"role": "user", "content": question}]

    with tracer.start_as_current_observation(
        as_type="span", name="agent-run", input={"question": question}
    ) as root:
        for step in range(1, max_steps + 1):
            with tracer.start_as_current_observation(
                as_type="generation", name="claude-call", model=MODEL, input=messages
            ) as generation:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                )
                generation.update(
                    output=[_dump(b) for b in response.content],
                    usage_details=_usage_of(response),
                )

            messages.append({"role": "assistant", "content": response.content})
            tool_uses = [b for b in response.content if getattr(b, "type", None) == "tool_use"]

            if not tool_uses:
                answer = _text_of(response.content)
                root.update(output=answer)
                return AgentResult(answer=answer, trace_id=root.trace_id, steps=step, messages=messages)

            tool_results = []
            for call in tool_uses:
                with tracer.start_as_current_observation(
                    as_type="span", name=f"tool:{call.name}", input=call.input
                ) as tool_span:
                    try:
                        result = call_tool(call.name, call.input)
                        is_error = False
                    except Exception as exc:  # the model gets the error, not a crash
                        result = str(exc)
                        is_error = True
                    tool_span.update(output=result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": str(result),
                    "is_error": is_error,
                })
            messages.append({"role": "user", "content": tool_results})

        answer = "(max steps exceeded without a final answer)"
        root.update(output=answer)
        return AgentResult(answer=answer, trace_id=root.trace_id, steps=max_steps, messages=messages)


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "What is 23 * 17?"
    result = run_agent(question)
    print(result.answer)
    print(f"steps: {result.steps}  trace_id: {result.trace_id}")
    get_tracer().flush()
