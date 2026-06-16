from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Type

from .capabilities.resolver import CapabilitiesResolver
from .context.presentation import IdentityPresentation
from .storage.factory import StorageRegistry
from .tools.exec_env import LocalExecEnvironment
from .tools.dispatcher import ToolDispatcher
from .tools.factory import create_tools
from .tools.protocol import ToolProtocol


# ---------------------------------------------------------------------------
# Config dataclasses
# ---------------------------------------------------------------------------

@dataclass
class StorageConfig:
    backend: str = "filesystem"
    root: Optional[Path] = None
    extra_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolsConfig:
    extras: list[ToolProtocol] = field(default_factory=list)


@dataclass
class CapabilitiesConfig:
    skill_catalog: Any = None
    resolve_timeout_seconds: float = 5.0
    # Providers de capabilities (Skills/MCP) — el integrador declara qué conectar.
    mcp_servers: dict[str, dict] = field(default_factory=dict)  # name -> raw server config
    skill_dirs: list[Path] = field(default_factory=list)        # raíces <dir>/<skill>/SKILL.md
    extra_providers: list[Any] = field(default_factory=list)    # CapabilityProvider adicionales


@dataclass
class ModelsConfig:
    extras: list = field(default_factory=list)  # list[agentic_models.Model]


@dataclass
class RuntimeConfig:
    storage: StorageConfig = field(default_factory=StorageConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    capabilities: CapabilitiesConfig = field(default_factory=CapabilitiesConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    model_caller: Any = None      # ModelCallerProtocol inyectado por el consumidor
    hook_runner: Any = None       # HookRunner inyectado por el consumidor
    task_registry: Any = None     # TaskRegistryProtocol inyectado por el consumidor
    presentation: Any = None      # PathPresentation inyectada por el consumidor (default identidad)
    exec_env: Any = None          # ToolExecEnvironment inyectado por el consumidor (default in-process)
    small_llm: Any = None
    model_id: str = ""
    background_result_max_chars: int = 2000


# ---------------------------------------------------------------------------
# RuntimeFactory — meta-factory con extension primitive
# ---------------------------------------------------------------------------

class RuntimeFactory:
    _modes: dict[str, Type] = {}

    @classmethod
    def register_execution_mode(cls, name: str, runtime_cls: Type) -> None:
        cls._modes[name] = name if False else runtime_cls

    @classmethod
    def _build_capability_manager(cls, caps: "CapabilitiesConfig") -> Any:
        """Ensambla el CapabilityManager con providers MCP/Skills declarados.

        Registra servers MCP y dirs de skills de forma tolerante (config inválida
        no aborta el ensamblado). Los servers MCP se CONECTAN en `manager.startup()`
        (lo invoca el integrador), no aquí — el factory no abre conexiones de red.
        """
        from .capabilities.manager import CapabilityManager
        from .capabilities.mcp import McpProvider
        from .capabilities.skills import SkillsProvider

        providers: list[Any] = []

        if caps.mcp_servers:
            mcp = McpProvider()
            mcp.load_servers(caps.mcp_servers)  # tolerante; conecta en startup()
            providers.append(mcp)

        if caps.skill_dirs:
            skills = SkillsProvider()
            for root in caps.skill_dirs:
                skills.load_dir(root)
            providers.append(skills)

        providers.extend(caps.extra_providers)
        return CapabilityManager(providers)

    @classmethod
    def _build_local(cls, config: RuntimeConfig) -> Any:
        from .execution.local import LocalAgentRuntime

        # Storage
        storage_kwargs: dict[str, Any] = {}
        if config.storage.root is not None:
            storage_kwargs["root"] = config.storage.root
        storage_kwargs.update(config.storage.extra_kwargs)
        storage = StorageRegistry.create(config.storage.backend, **storage_kwargs)

        # Tools nativas — input al ensamblado del pool, no lookup de ejecución
        tool_registry = create_tools(extras=config.tools.extras)

        # Capabilities: manager con providers (Skills/MCP). El pool por turno
        # converge native + capability vía manager.build_tool_pool (alineado a
        # assembleToolPool). Los providers se conectan en startup() (MCP) / al cargar.
        capability_manager = cls._build_capability_manager(config.capabilities)

        # Resolver legacy — conservado para compatibilidad; el loop usa el pool.
        capabilities_resolver = CapabilitiesResolver(
            tool_registry=tool_registry,
            skill_catalog=config.capabilities.skill_catalog,
            resolve_timeout_seconds=config.capabilities.resolve_timeout_seconds,
        )

        # Tool dispatch — único puente loop ↔ tools; resuelve desde ctx.tool_pool
        tool_dispatcher = ToolDispatcher()

        # Presentación de paths — default identidad (canónico CLI/IDE)
        presentation = config.presentation or IdentityPresentation()

        # Entorno de ejecución de tools — default in-process (canónico CLI/IDE)
        exec_env = config.exec_env or LocalExecEnvironment()

        return LocalAgentRuntime(
            model_caller=config.model_caller,
            tool_registry=tool_registry,
            capability_manager=capability_manager,
            capabilities_resolver=capabilities_resolver,
            tool_dispatcher=tool_dispatcher,
            task_registry=config.task_registry,
            hook_runner=config.hook_runner,
            storage=storage,
            presentation=presentation,
            exec_env=exec_env,
            small_llm=config.small_llm,
            background_result_max_chars=config.background_result_max_chars,
            model_id=config.model_id,
        )


def create_runtime(
    *,
    execution_mode: str = "local",
    config: Optional[RuntimeConfig] = None,
) -> Any:
    """
    Meta-factory que ensambla un runtime completo a partir de RuntimeConfig.

    El proyecto declara qué implementaciones inyectar; el runtime usa defaults si no se inyecta nada.
    """
    if config is None:
        config = RuntimeConfig()

    if execution_mode == "local":
        return RuntimeFactory._build_local(config)

    # Modos registrados por proyectos
    custom_cls = RuntimeFactory._modes.get(execution_mode)
    if custom_cls is not None:
        return custom_cls(config=config)

    if execution_mode in ("remote", "tmux", "kubernetes", "lambda"):
        raise NotImplementedError(f"execution_mode='{execution_mode}' no implementado aún")

    raise NotImplementedError(f"execution_mode='{execution_mode}' desconocido")
