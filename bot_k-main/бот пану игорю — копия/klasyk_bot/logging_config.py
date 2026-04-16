from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


class _MaskSecretFilter(logging.Filter):
    def __init__(self, secrets: list[str]) -> None:
        super().__init__()
        self._secrets = [s for s in secrets if s]

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if not msg:
            return True
        masked = msg
        for secret in self._secrets:
            if secret and secret in masked:
                masked = masked.replace(secret, "<SECRET>")
        # If we changed message content, put it back
        if masked != msg:
            record.msg = masked
            record.args = ()
        return True


def setup_logging(bot_token: str | None = None) -> Path:
    """
    Полное логирование: консоль + файл (rotating).
    Маскируем BOT_TOKEN, чтобы он не попал в логи.
    """
    base_dir = Path(__file__).resolve().parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "bot_full.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Убираем прошлые handlers (на случай повторного запуска в IDE)
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=str(log_path),
        mode="a",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    secrets = [bot_token] if bot_token else []
    filt = _MaskSecretFilter(secrets=secrets)
    file_handler.addFilter(filt)
    console_handler.addFilter(filt)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # PTB/HTTPX внутренности
    logging.getLogger("telegram").setLevel(logging.DEBUG)
    logging.getLogger("telegram.ext").setLevel(logging.DEBUG)
    logging.getLogger("httpx").setLevel(logging.DEBUG)

    return log_path

