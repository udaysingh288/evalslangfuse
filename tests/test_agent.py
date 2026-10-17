import tracing
from agent import run_agent
from fakes import FakeBlock, FakeResponse, ScriptedClient


def setup_function(_):
    # No Langfuse credentials are expected in the test environment; make sure
    # a stale real client from an earlier test doesn't leak in.
    tracing.reset_tracer_for_tests()


def test_direct_text_answer_needs_no_tool_call():
    client = ScriptedClient([FakeResponse(content=[FakeBlock(type="text", text="391")])])
    result = run_agent("What is 23*17?", client=client)
    assert result.answer == "391"
    assert result.steps == 1
    assert client.messages.calls == 1


def test_agent_uses_the_calculator_tool_then_answers():
    client = ScriptedClient([
        FakeResponse(content=[FakeBlock(type="tool_use", name="calculator", input={"expression": "23*17"}, id="t1")]),
        FakeResponse(content=[FakeBlock(type="text", text="391")]),
    ])
    result = run_agent("What is 23*17?", client=client)
    assert result.answer == "391"
    assert result.steps == 2
    tool_result_message = result.messages[-2]
    assert tool_result_message["role"] == "user"
    assert tool_result_message["content"][0]["content"] == "391"


def test_agent_reports_tool_errors_back_to_the_model_without_crashing():
    client = ScriptedClient([
        FakeResponse(content=[FakeBlock(type="tool_use", name="calculator", input={"expression": "a+1"}, id="t1")]),
        FakeResponse(content=[FakeBlock(type="text", text="I could not compute that.")]),
    ])
    result = run_agent("bad expression", client=client)
    assert "could not" in result.answer.lower()
    tool_result_message = result.messages[-2]
    assert tool_result_message["content"][0]["is_error"] is True


def test_agent_stops_after_max_steps_instead_of_looping_forever():
    responses = [
        FakeResponse(content=[FakeBlock(type="tool_use", name="calculator", input={"expression": "1+1"}, id="t1")])
        for _ in range(10)
    ]
    client = ScriptedClient(responses)
    result = run_agent("loop forever", client=client, max_steps=3)
    assert result.steps == 3
    assert "max steps" in result.answer
    assert client.messages.calls == 3


def test_trace_id_is_present_without_langfuse_credentials():
    client = ScriptedClient([FakeResponse(content=[FakeBlock(type="text", text="ok")])])
    result = run_agent("hi", client=client)
    assert result.trace_id
