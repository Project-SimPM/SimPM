import logging
from pathlib import Path

from simpm.log_cfg import LogConfig


def _file_handlers(logger: logging.Logger):
    return [handler for handler in logger.handlers if isinstance(handler, logging.FileHandler)]


def test_handlers_not_duplicated(tmp_path: Path):
    log_path = tmp_path / "simpm.log"

    first = LogConfig(enabled=True, file_path=str(log_path))
    first_count = len(first.logger.handlers)

    second = LogConfig(enabled=True, file_path=str(log_path))

    assert len(second.logger.handlers) == first_count
    assert len(_file_handlers(second.logger)) == 1


def test_file_handler_not_created_when_disabled(tmp_path: Path):
    log_path = tmp_path / "simpm_disabled.log"

    cfg = LogConfig(enabled=False, file_path=str(log_path))

    assert len(_file_handlers(cfg.logger)) == 0
    assert not log_path.exists()


def test_file_handler_optional(tmp_path: Path):
    cfg = LogConfig(enabled=True, file_path=None)

    assert len(_file_handlers(cfg.logger)) == 0
    assert len(cfg.logger.handlers) == 1
