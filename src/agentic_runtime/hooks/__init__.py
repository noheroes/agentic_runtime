"""Hooks del runtime — intercepción de ciclo de vida con decisión. Ver protocol.py."""
from .protocol import HookDecision, HookEvent, HookHandler, HookSinkProtocol
from .runner import HookRunner

__all__ = [
    "HookDecision",
    "HookEvent",
    "HookHandler",
    "HookRunner",
    "HookSinkProtocol",
]
