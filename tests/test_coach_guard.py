from core.coach.protocol import requires_guard


def test_guard_detects_final_answer_requests():
    assert requires_guard("Please give the final answer.")
    assert requires_guard("给出完整答案")
    assert not requires_guard("Explain the steps and framework.")
