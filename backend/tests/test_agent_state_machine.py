from app.agent_runtime.state_machine import RunStatus, transition


def test_waiting_states_can_resume_or_expire():
    assert transition(RunStatus.WAITING_FOR_USER_CONTEXT, RunStatus.EXECUTING) is RunStatus.EXECUTING
    assert transition(RunStatus.WAITING_FOR_APPROVAL, RunStatus.EXPIRED) is RunStatus.EXPIRED
    assert transition(RunStatus.WAITING_FOR_EXTERNAL_JOB, RunStatus.FAILED_RETRYABLE) is RunStatus.FAILED_RETRYABLE


def test_final_safety_can_repair_then_revalidate():
    assert transition(RunStatus.FINAL_SAFETY_VALIDATION, RunStatus.REPAIRING_RESPONSE) is RunStatus.REPAIRING_RESPONSE
    assert transition(RunStatus.REPAIRING_RESPONSE, RunStatus.FINAL_SAFETY_VALIDATION) is RunStatus.FINAL_SAFETY_VALIDATION
