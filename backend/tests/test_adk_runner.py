import asyncio

from app.agent_runtime.adk_runner import AdkAgentModelProvider, AdkInvocation, AdkRunner


class FakeRunner:
    def run_async(self, **kwargs):
        async def events():
            yield {"session_id": kwargs["session_id"], "message": kwargs["new_message"]}
        return events()


def test_adk_runner_is_injectable_and_collects_events():
    runner = AdkRunner(object(), runner=FakeRunner())
    events = asyncio.run(runner.run(AdkInvocation("owner", "session", "compare evidence")))
    assert events[0]["session_id"] == "session"

def test_adk_runner_bounds_event_stream():
    class EndlessRunner:
        def run_async(self, **kwargs):
            async def events():
                index = 0
                while True:
                    yield {"index": index}
                    index += 1
            return events()
    events = asyncio.run(AdkRunner(object(), runner=EndlessRunner(), max_events=3).run(AdkInvocation("u", "s", "x")))
    assert [event["index"] for event in events] == [0, 1, 2]

def test_adk_agent_model_provider_extracts_structured_output():
    class StructuredRunner:
        def run_async(self, **kwargs):
            async def events():
                yield {"request_id": "req-1", "structured_payload": {"usable": True}}
            return events()
    provider = AdkAgentModelProvider(AdkRunner(object(), runner=StructuredRunner()), user_id="u", session_id="s")
    result = provider.invoke(role="EVIDENCE_INTAKE", model_binding="gemini", prompt_version="v1", context_bundle={"asset": "a"}, tool_declarations=[], response_schema=dict, timeout_seconds=5)
    assert result.structured_payload == {"usable": True} and result.provider_request_id == "req-1"

def test_adk_agent_model_provider_enforces_timeout():
    class SlowRunner:
        async def _wait(self):
            await asyncio.sleep(0.05)
            return []
        def run_async(self, **kwargs):
            return self._wait()
    provider = AdkAgentModelProvider(AdkRunner(object(), runner=SlowRunner()), user_id="u", session_id="s")
    try:
        provider.invoke(role="EVIDENCE_INTAKE", model_binding="gemini", prompt_version="v1", context_bundle={}, tool_declarations=[], response_schema=dict, timeout_seconds=0.001)
    except TimeoutError as exc:
        assert str(exc) == "ADK_INVOCATION_TIMEOUT"
    else:
        raise AssertionError("slow ADK invocation was not bounded")
