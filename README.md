# simple-agent

A single agent — a financial document summarizer — built with LangChain's
`create_agent`, wrapped in two middlewares:

- **SummarizationMiddleware**: compresses old conversation turns once the
  message history passes a token threshold, so long sessions don't blow the
  context window.
- **HumanInTheLoopMiddleware**: pauses before the `process_payment` tool
  runs, with escalation logic (`escalate_large_payment` in `agent.py`) that
  only routes payments above `ESCALATION_THRESHOLD` to a human for
  approval; smaller ones are auto-approved.

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

- `ANTHROPIC_API_KEY`: required.
- `ESCALATION_THRESHOLD`: dollar amount above which a payment needs human
  approval (default `1000`).

## Run

```bash
./.venv/bin/python agent.py "Invoice #12: pay Acme $2,000 for services rendered."
```

With no argument, it summarizes a built-in sample invoice. If the document
asks for a payment above the threshold, you'll be prompted in the terminal
to approve or reject it before the agent continues.

## Files

| File        | What it is                                             |
| ----------- | ------------------------------------------------------- |
| `agent.py`  | The agent, its middleware, and the CLI loop.             |
| `tools.py`  | `process_payment`, the one tool the agent can call.      |
