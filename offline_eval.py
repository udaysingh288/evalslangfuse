"""Offline evaluation: run the agent over a fixed dataset and score each answer.

With LANGFUSE_PUBLIC_KEY/SECRET_KEY set, this runs as a Langfuse Experiment,
visible on the Experiments page of your Langfuse project, with one trace per
dataset item. Without them, it still runs and prints the same scores here.

Run: python offline_eval.py
"""

from dataset import DATASET
from agent import run_agent
from evaluators import contains_expected
from tracing import get_tracer, tracing_enabled


def task(*, item, **kwargs):
    return run_agent(item["input"]).answer


def _run_locally():
    rows = []
    for item in DATASET:
        answer = task(item=item)
        value, comment = contains_expected(answer, item["expected_output"])
        rows.append((item["input"], item["expected_output"], answer, value, comment))

    passed = sum(1 for row in rows if row[3] == 1.0)
    print(f"{passed}/{len(rows)} passed\n")
    for question, expected, answer, value, comment in rows:
        status = "PASS" if value == 1.0 else "FAIL"
        print(f"[{status}] {question}")
        print(f"   expected: {expected!r}  got: {answer!r}")
        if value != 1.0:
            print(f"   {comment}")
    return rows


def _run_as_experiment(tracer):
    def evaluator(*, input, output, expected_output, metadata=None, **kwargs):
        from langfuse import Evaluation

        value, comment = contains_expected(output, expected_output)
        return Evaluation(name="contains_expected", value=value, comment=comment)

    result = tracer.run_experiment(
        name="simple-agent-offline-eval",
        description="Does the agent's answer contain the expected text?",
        data=DATASET,
        task=task,
        evaluators=[evaluator],
    )
    print(result.format())
    tracer.flush()


def main():
    tracer = get_tracer()
    if tracing_enabled():
        _run_as_experiment(tracer)
    else:
        print("LANGFUSE_PUBLIC_KEY/SECRET_KEY not set: running locally, no Experiment is recorded.\n")
        _run_locally()


if __name__ == "__main__":
    main()
