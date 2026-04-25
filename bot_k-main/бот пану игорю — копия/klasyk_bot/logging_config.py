from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── Budget ────────────────────────────────────────────────────────────────────
# General log : 200 MB × 10 = 2 GB max  (INFO+)
# Error   log : 100 MB × 10 = 1 GB max  (ERROR+)
# Console     : INFO, compact one-liner
_GENERAL_MAX   = 200 * 1024 * 1024   # 200 MB per file
_GENERAL_COUNT = 9                    # +1 active = 10 files
_ERROR_MAX     = 100 * 1024 * 1024   # 100 MB per file
_ERROR_COUNT   = 9                    # +1 active = 10 files

# ── Compact format (glog-inspired) ───────────────────────────────────────────
# I0420 14:30:05 module|message
_COMPACT_FMT  = "%(levelname).1s%(asctime)s %(name)s|%(message)s"
_COMPACT_DATE  = "%m%d %H:%M:%S"


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
                masked = masked.replace(secret, "<SEC>")
        if masked != msg:
            record.msg = masked
            record.args = ()
        return True


def setup_logging(bot_token: str | None = None) -> Path:
    """Configure production logging: compact format, 2 GB general + 1 GB errors."""
    base_dir = Path(__file__).resolve().parent
    _env_suffix = os.getenv("BOT_ENV", "")
    logs_dir = base_dir / (f"logs_{_env_suffix}" if _env_suffix else "logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_path = logs_dir / "bot.log"
    err_path = logs_dir / "error.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(fmt=_COMPACT_FMT, datefmt=_COMPACT_DATE)
    secrets = [bot_token] if bot_token else []
    filt = _MaskSecretFilter(secrets=secrets)

    # ── General log (INFO+) → 2 GB total ─────────────────────────────────
    fh = RotatingFileHandler(
        str(log_path), mode="a",
        maxBytes=_GENERAL_MAX, backupCount=_GENERAL_COUNT,
        encoding="utf-8",
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    fh.addFilter(filt)
    root.addHandler(fh)

    # ── Error log (ERROR+) → 1 GB total ──────────────────────────────────
    eh = RotatingFileHandler(
        str(err_path), mode="a",
        maxBytes=_ERROR_MAX, backupCount=_ERROR_COUNT,
        encoding="utf-8",
    )
    eh.setLevel(logging.ERROR)
    eh.setFormatter(fmt)
    eh.addFilter(filt)
    root.addHandler(eh)

    # ── Console (INFO+, same compact format) → goes to journald ──────────
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)
    ch.addFilter(filt)
    root.addHandler(ch)

    # Silence noisy libraries
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("telegram.ext").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return log_path

