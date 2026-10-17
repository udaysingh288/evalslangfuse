import tracing


def test_null_tracer_is_used_without_credentials(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    tracing.reset_tracer_for_tests()
    assert tracing.tracing_enabled() is False


def test_null_tracer_context_manager_yields_a_usable_span():
    tracer = tracing.NullTracer()
    with tracer.start_as_current_observation(as_type="span", name="x") as span:
        span.update(output="anything")  # must not raise
        span.score_trace(name="y", value=1.0)  # must not raise
        assert isinstance(span.trace_id, str) and span.trace_id

    tracer.create_score(trace_id="x", name="y", value=1.0)  # must not raise
    tracer.flush()  # must not raise


def test_get_tracer_is_cached(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    tracing.reset_tracer_for_tests()
    assert tracing.get_tracer() is tracing.get_tracer()


def test_reset_clears_the_cache(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    tracing.reset_tracer_for_tests()
    first = tracing.get_tracer()
    tracing.reset_tracer_for_tests()
    second = tracing.get_tracer()
    assert first is not second
