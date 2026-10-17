"""Minimal stand-ins for Anthropic SDK objects: just the attributes agent.py reads."""

from dataclasses import dataclass, field


@dataclass
class FakeUsage:
    input_tokens: int = 10
    output_tokens: int = 5


@dataclass
class FakeBlock:
    type: str
    text: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)
    id: str = "tool_1"

    def model_dump(self):
        return {"type": self.type, "text": self.text, "name": self.name, "input": self.input}


@dataclass
class FakeResponse:
    content: list
    usage: FakeUsage = field(default_factory=FakeUsage)


class ScriptedMessages:
    """Stands in for client.messages: returns queued responses in order."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if not self._responses:
            raise AssertionError("ScriptedClient ran out of queued responses")
        return self._responses.pop(0)


class ScriptedClient:
    def __init__(self, responses):
        self.messages = ScriptedMessages(responses)
