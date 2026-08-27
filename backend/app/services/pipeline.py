from collections.abc import Callable


class AnalysisOrchestrator:
    def __init__(
        self,
        prepare: Callable[[object], object],
        ai: Callable[[object], object],
        validate: Callable[[object], object],
        guardrails: Callable[[object], object],
        safety: Callable[[object], object],
        persist: Callable[[object], object],
    ):
        self.stages = (prepare, ai, validate, guardrails, safety, persist)

    def run(self, payload: object) -> object:
        result = payload
        for stage in self.stages:
            result = stage(result)
        return result
