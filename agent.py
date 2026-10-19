"""A financial document summarizer agent with two middlewares:

- SummarizationMiddleware: compresses old conversation turns once the message
  history grows past a threshold, so a long session doesn't blow the context
  window.
- HumanInTheLoopMiddleware: pauses before `process_payment` runs. Escalation
  logic (`escalate_large_payment`) only routes payments above
  ESCALATION_THRESHOLD to a human; smaller ones are auto-approved.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from tools import process_payment

MODEL = os.environ.get("MODEL_NAME", "claude-sonnet-5")
ESCALATION_THRESHOLD = float(os.environ.get("ESCALATION_THRESHOLD", "1000"))

SYSTEM_PROMPT = (
    "You are a financial document summarizer. Read the document the user gives you and "
    "produce a short, clear summary of its key figures, obligations, and dates. If the "
    "document instructs that a payment be made, call process_payment with the payee, "
    "amount, and a short memo."
)


def escalate_large_payment(request) -> bool:
    """Escalation logic: only payments over the threshold need a human."""
    return request.tool_call["args"].get("amount", 0) > ESCALATION_THRESHOLD


def build_agent():
    return create_agent(
        MODEL,
        tools=[process_payment],
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            SummarizationMiddleware(model=MODEL, trigger=("tokens", 3000), keep=("messages", 10)),
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "process_payment": {
                        "allowed_decisions": ["approve", "reject"],
                        "when": escalate_large_payment,
                    }
                },
            ),
        ],
        checkpointer=InMemorySaver(),
    )


def _print_action_requests(interrupt_value: dict) -> None:
    print("\n--- Human approval required ---")
    for req in interrupt_value["action_requests"]:
        print(f"  tool: {req['name']}  args: {req['args']}")
    print("--------------------------------")


def _ask_decisions(interrupt_value: dict) -> dict:
    decisions = []
    for req in interrupt_value["action_requests"]:
        args = req["args"]
        prompt = f"Approve payment of ${args.get('amount')} to {args.get('payee')}? [y/n]: "
        while True:
            choice = input(prompt).strip().lower()
            if choice in ("y", "yes"):
                decisions.append({"type": "approve"})
                break
            if choice in ("n", "no"):
                decisions.append({"type": "reject", "message": "Rejected by human reviewer."})
                break
    return {"decisions": decisions}


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if block.get("type") == "text")


def run(document: str, thread_id: str = "cli-session") -> str:
    agent = build_agent()
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [{"role": "user", "content": document}]}, config)

    while "__interrupt__" in result:
        interrupt = result["__interrupt__"][0]
        _print_action_requests(interrupt.value)
        resume = _ask_decisions(interrupt.value)
        result = agent.invoke(Command(resume=resume), config)

    return _text_of(result["messages"][-1].content)


SAMPLE_DOCUMENT = (
    "Invoice #4521 from Acme Consulting: advisory services rendered in Q3, "
    "amount due $1,500, payable to Acme Consulting by October 31. A separate "
    "reimbursement of $85 for office supplies is also due to employee J. Rivera."
)

if __name__ == "__main__":
    document = " ".join(sys.argv[1:]) or SAMPLE_DOCUMENT
    print(run(document))
