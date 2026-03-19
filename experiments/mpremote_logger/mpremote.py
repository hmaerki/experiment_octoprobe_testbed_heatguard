from __future__ import annotations

import functools
import inspect


def call_logger(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        mp_remote = args[0]  # Remove the self parameter
        assert isinstance(mp_remote, MpRemote)
        call_logger = mp_remote.call_logger

        bound = inspect.signature(func).bind(*args, **kwargs)
        bound.apply_defaults()

        mp_remote.call_logger.enter()
        func_text = ", ".join(
            f"{k}={v!r}" for k, v in bound.arguments.items() if k != "self"
        )
        call_logger.log_call(func_text=func_text)
        try:
            result = func(*args, **kwargs)
            call_logger.log_return(result=result)
            return result
        except Exception as e:
            call_logger.log_exception(e)
            raise
        finally:
            call_logger.leave()

    return wrapper


class CallLogger:
    def __init__(self, MpRemote: MpRemote) -> None:
        self.level = 0
        self._MpRemote = MpRemote

    @property
    def indent(self) -> str:
        return self._MpRemote._label + " " + "    " * self.level

    def log_call(self, func_text: str) -> None:
        self._log(sep=">>", text=func_text)

    def log_return(self, result: str) -> None:
        self._log(sep="<<", text=result)

    def log_exception(self, e: Exception) -> None:
        self._log(sep="!!", text="raised {e!r}")

    def _log(self, sep: str, text: str) -> None:
        print(f"{self.indent}{sep} {text}")

    def enter(self) -> None:
        self.level += 1

    def leave(self) -> None:
        self.level -= 1


class MpRemote:
    def __init__(self, label: str) -> None:
        self._label = label
        self.call_logger = CallLogger(MpRemote=self)

    @call_logger
    def level_0_a(self, expr: str) -> float:
        value_text = self.level_1_a(expr=f"1/{expr}")
        value = eval(value_text)
        assert isinstance(value, float), value
        return value

    @call_logger
    def level_1_a(self, expr: str) -> str:
        return self.eval_raw(cmd=f"{expr}*{expr}")

    @call_logger
    def eval_raw(self, cmd: str) -> str:
        return cmd


def main() -> None:
    mp = MpRemote(label="dut")
    mp.level_0_a("3+7")


if __name__ == "__main__":
    main()
