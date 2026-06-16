"""Hooks del runtime — intercepción de ciclo de vida con decisión. Ver protocol.py."""
from .protocol import HookDecision, HookEvent, HookHandler, HookSinkProtocol
from .runner import HookRunner

__all__ = [
    "HookEvent",
    "HookDecision",
    "HookHandler",
    "HookSinkProtocol",
    "HookRunner",
]
