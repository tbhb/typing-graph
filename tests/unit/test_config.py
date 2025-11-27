from typing_extensions import Format

from typing_graph import EvalMode, InspectConfig


class TestGetFormat:
    def test_eager_mode_returns_format_value(self) -> None:
        config = InspectConfig(eval_mode=EvalMode.EAGER)
        assert config.get_format() == Format.VALUE

    def test_deferred_mode_returns_format_forwardref(self) -> None:
        config = InspectConfig(eval_mode=EvalMode.DEFERRED)
        assert config.get_format() == Format.FORWARDREF

    def test_stringified_mode_returns_format_string(self) -> None:
        config = InspectConfig(eval_mode=EvalMode.STRINGIFIED)
        assert config.get_format() == Format.STRING
