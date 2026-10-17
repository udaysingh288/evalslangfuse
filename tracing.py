"""Thin wrapper around the Langfuse client.

Everything that talks to Langfuse goes through get_tracer(), and it falls
back to a no-op tracer when LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are not
set. That means the agent, the tests, and even the eval scripts' local
fallback path all run with no Langfuse account at all; set the two keys when
you want real traces, experiments, and scores.
"""

import os
import uuid
from contextlib import contextmanager

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class NullSpan:
    def __init__(self):
        self.trace_id = f"disabled-{uuid.uuid4()}"
        self.id = self.trace_id

    def update(self, **kwargs):
        pass

    def score_trace(self, **kwargs):
        pass


class NullTracer:
    """Used when Langfuse credentials are not configured. Every call is a no-op."""

    enabled = False

    @contextmanager
    def start_as_current_observation(self, **kwargs):
        yield NullSpan()

    def create_score(self, **kwargs):
        pass

    def flush(self):
        pass


_tracer = None


def get_tracer():
    """Return the real Langfuse client if credentials are set, else a no-op tracer."""
    global _tracer
    if _tracer is not None:
        return _tracer
    if os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"):
        from langfuse import get_client

        _tracer = get_client()
    else:
        _tracer = NullTracer()
    return _tracer


def tracing_enabled() -> bool:
    """True when get_tracer() returned the real Langfuse client, not the no-op one."""
    return not isinstance(get_tracer(), NullTracer)


def reset_tracer_for_tests():
    """Clear the cached tracer so the next get_tracer() call re-reads the environment."""
    global _tracer
    _tracer = None
