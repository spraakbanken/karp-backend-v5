from karp5.application.actions.mode_actions import recover


def test_mode_action_recover():
    result = recover("panacea")

    assert result == "Ok"
