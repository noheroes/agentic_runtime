from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

LOCK_STALE_SECONDS = 10.0
LOCK_POLL_SECONDS = 0.01
LOCK_TIMEOUT_SECONDS = 5.0
SLOW_LOCK_SECONDS = 0.1
MIN_BACKUP_INTERVAL_MS = 60_000
MAX_BACKUPS = 5

Merge = Callable[[dict[str, Any]], dict[str, Any]]


class ConfigLockError(RuntimeError):
    pass


class ConfigStore:
    def __init__(self, path: Any, *, defaults: dict[str, Any] | None = None) -> None:
        self.path = Path(path)
        self._defaults = dict(defaults or {})

    def defaults(self) -> dict[str, Any]:
        return dict(self._defaults)

    def read(self) -> dict[str, Any]:
        try:
            content = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return dict(self._defaults)
        except OSError as exc:
            logger.error("config: no se pudo leer %s: %s", self.path, exc)
            return dict(self._defaults)
        return self._parse(content)

    def update(self, merge: Merge) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        release = self._lock()
        try:
            current = self.read()
            merged = merge(current)
            if merged is current:
                return False
            filtered = {
                key: value
                for key, value in merged.items()
                if json.dumps(value, sort_keys=True)
                != json.dumps(self._defaults.get(key), sort_keys=True)
            }
            self._backup()
            self._write(filtered)
            return True
        finally:
            release()

    def _parse(self, content: str) -> dict[str, Any]:
        try:
            parsed = json.loads(content.lstrip("﻿"))
        except json.JSONDecodeError as exc:
            logger.error(
                "config: %s corrupto, se usan los valores por defecto: %s", self.path, exc
            )
            self._backup_corrupted(content)
            return dict(self._defaults)
        if not isinstance(parsed, dict):
            logger.error("config: %s no contiene un objeto JSON", self.path)
            self._backup_corrupted(content)
            return dict(self._defaults)
        return {**self._defaults, **parsed}

    def _backup_dir(self) -> Path:
        return self.path.parent / "backups"

    def _backup(self) -> None:
        try:
            if not self.path.exists():
                return
            directory = self._backup_dir()
            directory.mkdir(parents=True, exist_ok=True)
            prefix = f"{self.path.name}.backup."
            existing = sorted(
                (entry for entry in os.listdir(directory) if entry.startswith(prefix)),
                reverse=True,
            )
            most_recent = existing[0] if existing else None
            try:
                stamp = int(most_recent.rsplit(".backup.", 1)[1]) if most_recent else 0
            except ValueError:
                stamp = 0
                most_recent = None
            now = int(time.time() * 1000)
            if most_recent is None or now - stamp >= MIN_BACKUP_INTERVAL_MS:
                (directory / f"{prefix}{now}").write_bytes(self.path.read_bytes())
                existing = sorted(
                    (entry for entry in os.listdir(directory) if entry.startswith(prefix)),
                    reverse=True,
                )
            for stale in existing[MAX_BACKUPS:]:
                try:
                    (directory / stale).unlink()
                except OSError:
                    pass
        except OSError as exc:
            logger.error("config: no se pudo respaldar %s: %s", self.path, exc)

    def _backup_corrupted(self, content: str) -> None:
        try:
            directory = self._backup_dir()
            directory.mkdir(parents=True, exist_ok=True)
            prefix = f"{self.path.name}.corrupted."
            for entry in os.listdir(directory):
                if not entry.startswith(prefix):
                    continue
                if (directory / entry).read_text(encoding="utf-8", errors="replace") == content:
                    return
            target = directory / f"{prefix}{int(time.time() * 1000)}"
            target.write_text(content, encoding="utf-8")
            logger.error("config: copia del fichero corrupto en %s", target)
        except OSError as exc:
            logger.error("config: no se pudo respaldar el fichero corrupto: %s", exc)

    def _write(self, payload: dict[str, Any]) -> None:
        descriptor = os.open(
            self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            handle.flush()
            os.fsync(handle.fileno())

    def _lock(self) -> Callable[[], None]:
        lock_path = self.path.with_name(self.path.name + ".lock")
        started = time.monotonic()
        while True:
            try:
                os.mkdir(lock_path)
                break
            except FileExistsError:
                try:
                    age = time.time() - lock_path.stat().st_mtime
                except FileNotFoundError:
                    continue
                if age > LOCK_STALE_SECONDS:
                    logger.error("config: lock caducado en %s, se retoma", lock_path)
                    try:
                        os.rmdir(lock_path)
                    except OSError:
                        pass
                    continue
                if time.monotonic() - started > LOCK_TIMEOUT_SECONDS:
                    raise ConfigLockError(
                        f"no se pudo tomar el lock de configuración: {lock_path}"
                    ) from None
                time.sleep(LOCK_POLL_SECONDS)
        waited = time.monotonic() - started
        if waited > SLOW_LOCK_SECONDS:
            logger.warning(
                "config: tomar el lock tardó %.0f ms — puede haber otra instancia escribiendo",
                waited * 1000,
            )

        def release() -> None:
            try:
                os.rmdir(lock_path)
            except OSError:
                pass

        return release


__all__ = ["ConfigLockError", "ConfigStore"]
