"""Small compatibility boundary for invoking Google ADK.

PETi owns durable state; this adapter owns only session/event execution. It is
dependency-injectable so tests never need network credentials.
"""
import asyncio
import inspect
import json
from dataclasses import dataclass
from typing import Any

from .agent_model_provider import ProviderInvocationResult


class AdkUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class AdkInvocation:
    user_id: str
    session_id: str
    text: str
    role: str | None = None


class AdkRunner:
    def __init__(self, agent: Any, *, runner: Any | None = None, app_name: str = "peti", max_events: int = 64):
        if max_events < 1:
            raise ValueError("ADK_MAX_EVENTS_INVALID")
        self.agent = agent
        self.app_name = app_name
        self.max_events = max_events
        if runner is not None:
            self.runner = runner
            self.sessions = None
            return
        try:
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
        except ModuleNotFoundError as exc:
            raise AdkUnavailable("GOOGLE_ADK_NOT_INSTALLED") from exc
        self.sessions = InMemorySessionService()
        self.runner = Runner(agent=agent, app_name=app_name, session_service=self.sessions)

    async def run(self, invocation: AdkInvocation):
        """Run one bounded invocation and return ADK events unchanged."""
        if self.sessions is not None:
            await self.sessions.create_session(
                app_name=self.app_name,
                user_id=invocation.user_id,
                session_id=invocation.session_id,
            )
        message = self._message(invocation.text)
        selected = getattr(self.agent, "role_agents", {}).get(invocation.role, self.agent) if invocation.role else self.agent
        runner = self.runner
        if selected is not self.agent and self.sessions is not None:
            from google.adk.runners import Runner
            runner = Runner(agent=selected, app_name=self.app_name, session_service=self.sessions)
        result = runner.run_async(
            user_id=invocation.user_id,
            session_id=invocation.session_id,
            new_message=message,
        )
        if inspect.isawaitable(result):
            result = await result
        if hasattr(result, "__aiter__"):
            events = []
            async for event in result:
                events.append(event)
                if len(events) >= self.max_events:
                    break
            return events
        return result

    @staticmethod
    def _message(text: str):
        try:
            from google.genai import types
            return types.Content(role="user", parts=[types.Part.from_text(text=text)])
        except ModuleNotFoundError:
            return {"role": "user", "parts": [{"text": text}]}


class AdkAgentModelProvider:
    """Synchronous role-provider adapter over the bounded ADK event runner."""

    def __init__(self, runner: AdkRunner, *, user_id: str | None = None, session_id: str | None = None, provider="GOOGLE_ADK"):
        self.runner, self.user_id, self.session_id, self.provider = runner, user_id, session_id, provider

    def invoke(self, *, role, model_binding, prompt_version, context_bundle, tool_declarations, response_schema, timeout_seconds):
        request = {
            "role": role, "prompt_version": prompt_version,
            "context": context_bundle, "tools": tool_declarations,
            "response_schema": getattr(response_schema, "model_json_schema", dict)(),
        }
        bundle = context_bundle if isinstance(context_bundle, dict) else {}
        user_id = self.user_id or str(bundle.get("owner_user_id", "unknown-owner"))
        session_id = self.session_id or str(bundle.get("session_id", bundle.get("run_id", "unknown-session")))
        if timeout_seconds <= 0:
            raise ValueError("ADK_TIMEOUT_INVALID")
        invocation = AdkInvocation(user_id, session_id, json.dumps(request, separators=(",", ":")), role)
        async def bounded_run():
            return await asyncio.wait_for(self.runner.run(invocation), timeout=timeout_seconds)
        try:
            events = asyncio.run(bounded_run())
        except TimeoutError as exc:
            raise TimeoutError("ADK_INVOCATION_TIMEOUT") from exc
        payload = None
        request_id = None
        for event in events if isinstance(events, list) else [events]:
            if isinstance(event, dict):
                candidate = event.get("structured_payload") or event.get("payload") or event.get("output")
                if isinstance(candidate, dict): payload, request_id = candidate, event.get("request_id") or request_id
                elif isinstance(candidate, str):
                    try: payload = json.loads(candidate)
                    except (TypeError, ValueError): pass
            else:
                candidate = getattr(event, "structured_payload", None) or getattr(event, "payload", None)
                if isinstance(candidate, dict): payload = candidate
        if not isinstance(payload, dict):
            raise TypeError("ADK_STRUCTURED_OUTPUT_MISSING")
        return ProviderInvocationResult(self.provider, str(model_binding), request_id, payload, {}, finish_metadata={"role": role})
