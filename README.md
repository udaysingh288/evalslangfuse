# simple-agent-langfuse

A minimal tool-using agent, built directly on the Anthropic SDK with no agent
framework, instrumented with Langfuse so you can run both kinds of evaluation
on it yourself:

- **Offline evaluation**: run the agent over a fixed dataset of questions with
  known answers, and score each one. This is `offline_eval.py`.
- **Online evaluation**: score a single real run right after it happens, the
  way you'd score live traffic. This is `online_eval.py`.

## What the agent does

It answers questions using two tools: `calculator` (exact arithmetic) and
`count_letters` (exact letter counts). Both are things models get wrong on
their own, so you can see the tool calls doing real work in the trace.

The loop in `agent.py` is about 40 lines: call Claude, and if it asks for a
tool, run it and send the result back; otherwise return the text. Every
Claude call and every tool call is wrapped in a Langfuse observation, so one
run produces one trace with child spans for each model call and tool call.

## Setup

```bash
cd simple-agent-langfuse
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

- `ANTHROPIC_API_KEY`: required to actually call the model.
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`: optional. Get a free account
  at https://cloud.langfuse.com, create a project, and copy its keys. Without
  these two, everything still runs: `tracing.py` falls back to a no-op
  tracer, so you can try the agent and both eval scripts with no Langfuse
  account at all, before deciding to wire it up for real.

## Run the agent once

```bash
./.venv/bin/python agent.py "What is 23 * 17?"
```

Prints the answer, the number of steps, and a trace ID. With Langfuse keys
set, that trace is in your project's Tracing view.

## Offline evaluation

```bash
./.venv/bin/python offline_eval.py
```

Runs the agent over the six questions in `dataset.py` and checks whether each
answer contains the expected text (`evaluators.contains_expected`). With
Langfuse keys set, this runs as a **Langfuse Experiment**: open your
project's Experiments page and you'll see one row per dataset item, each
linked to its trace, with the score attached. Without keys, the same pass/fail
table prints to the terminal instead.

Edit `dataset.py` to add your own questions.

## Online evaluation

```bash
# score one request with a free, deterministic heuristic
./.venv/bin/python online_eval.py "How many letters are in 'strawberry'?"

# score it with a second model call (an LLM-as-judge) instead
./.venv/bin/python online_eval.py "How many letters are in 'strawberry'?" --judge

# score recent traces that don't have a score yet (needs Langfuse keys)
./.venv/bin/python online_eval.py --sweep
```

The first two run the agent once and attach a score to that run's trace with
`langfuse.create_score()`. That's the pattern for scoring real traffic as it
happens. `--sweep` is a stand-in for a scheduled job: it lists recent traces
through the Langfuse API and scores any that don't have a score yet, which is
closer to how you'd actually monitor production without scoring every single
request inline.

`heuristic_quality` is free and instant: it checks the answer isn't empty,
isn't a refusal, and isn't absurdly long. `judge_quality` asks the model to
rate the answer 0 to 1, which costs an extra call and is only a demo judge,
not a production-grade one.

## Tests

```bash
./.venv/bin/python -m pytest
```

36 tests, none of which need an API key or a Langfuse account: the Anthropic
client and the Langfuse tracer are both swapped for fakes (`tests/fakes.py`
and `tracing.NullTracer`).

## Files

| File | What it is |
| --- | --- |
| `agent.py` | The tool-use loop and Langfuse instrumentation. |
| `tools.py` | `calculator` and `count_letters`, plus their tool schemas. |
| `tracing.py` | Gets the Langfuse client, or a no-op tracer if no keys are set. |
| `evaluators.py` | The three scoring functions. |
| `dataset.py` | The offline eval dataset. |
| `offline_eval.py` | Runs the dataset through the agent and scores it. |
| `online_eval.py` | Scores one live run, or sweeps unscored traces. |
| `tests/` | Unit tests, all offline. |
