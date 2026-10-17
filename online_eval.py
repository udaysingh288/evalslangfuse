"""Online evaluation: score a live agent run right after it happens.

python online_eval.py "question"            score one request with the free heuristic
python online_eval.py "question" --judge    score it with a second model call instead
python online_eval.py --sweep               score recent unscored traces already in Langfuse

The per-request path is what you'd call right after serving a real user; the
sweep is a stand-in for a scheduled job that catches anything not scored yet.
Both need LANGFUSE_PUBLIC_KEY/SECRET_KEY to actually attach anything.
"""

import argparse

from agent import run_agent
from evaluators import heuristic_quality, judge_quality
from tracing import get_tracer, tracing_enabled


def score_one(question: str, use_judge: bool = False):
    tracer = get_tracer()
    result = run_agent(question)
    if use_judge:
        value, comment = judge_quality(question, result.answer)
        name = "online_quality_judge"
    else:
        value, comment = heuristic_quality(question, result.answer)
        name = "online_quality_heuristic"

    tracer.create_score(trace_id=result.trace_id, name=name, value=value, comment=comment)
    tracer.flush()
    return result, value, comment


def sweep_unscored(limit: int = 20, use_judge: bool = False):
    """Score recent traces that have no score yet."""
    tracer = get_tracer()
    if not tracing_enabled():
        print("LANGFUSE_PUBLIC_KEY/SECRET_KEY not set: there is nothing to sweep.")
        return

    try:
        traces = tracer.api.trace.list(name="agent-run", limit=limit).data
    except Exception as exc:
        print(f"Could not list traces ({exc}). The API may have moved; check the Langfuse docs.")
        return

    scored = 0
    for trace in traces:
        if trace.scores:
            continue
        question = (trace.input or {}).get("question", "")
        answer = trace.output or ""
        value, comment = judge_quality(question, answer) if use_judge else heuristic_quality(question, answer)
        tracer.create_score(trace_id=trace.id, name="online_quality_sweep", value=value, comment=comment)
        scored += 1
    tracer.flush()
    print(f"scored {scored} previously unscored trace(s) out of {len(traces)} checked")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question", nargs="*", help="question to ask the agent")
    parser.add_argument("--judge", action="store_true", help="score with a model call instead of the free heuristic")
    parser.add_argument("--sweep", action="store_true", help="score recent unscored traces instead of asking one")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.sweep:
        sweep_unscored(limit=args.limit, use_judge=args.judge)
        return

    question = " ".join(args.question) or "What is 23 * 17?"
    result, value, comment = score_one(question, use_judge=args.judge)
    print(result.answer)
    print(f"score: {value}  ({comment})")
    print(f"trace_id: {result.trace_id}")


if __name__ == "__main__":
    main()
