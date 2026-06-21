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
    # Puertos de persistencia (dónde se guardan el registro de MCP y los skills). Los
    # inyecta quien integra el runtime; si None, se usa el default sobre StorageProtocol.
    mcp_config_store: Any = None
    skill_store: Any = None
    # Memoria del agente: dir raíz en disco (default `FilesystemMemoryStore`) o un
    # `MemoryStore` inyectado. Si alguno está presente, se registra `MemoryProvider`.
    memory_root: Optional[Path] = None
    memory_store: Any = None
    # Auth OAuth de MCP: handlers interactivos inyectados por el integrador (el runtime
    # headless no abre navegador). TokenStorage por defecto = sobre StorageProtocol.
    mcp_oauth_redirect_handler: Any = None
    mcp_oauth_callback_handler: Any = None


@dataclass
class ModelsConfig:
    extras: list = field(default_factory=list)  # list[agentic_models.Model]


@dataclass
class VoiceConfig:
    """I/O por voz (STT/TTS). Las primitivas las inyecta el integrador; cada canal
    se activa/desactiva por config sin retirar la implementación inyectada.

    - `stt`: `SpeechToTextProtocol` — transcribe el audio de la task a prompt.
    - `tts`: `TextToSpeechProtocol` — recibe la salida saneada, incremental.
    Un canal está ACTIVO sii su primitiva está inyectada y su flag `*_enabled`."""

    stt: Any = None
    tts: Any = None
    stt_enabled: bool = True
    tts_enabled: bool = True


@dataclass
class RuntimeConfig:
    storage: StorageConfig = field(default_factory=StorageConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    capabilities: CapabilitiesConfig = field(default_factory=CapabilitiesConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    model_caller: Any = None      # ModelCallerProtocol inyectado por el consumidor
    hook_runner: Any = None       # HookRunner inyectado por el consumidor
    task_registry: Any = None     # TaskRegistryProtocol inyectado por el consumidor
    presentation: Any = None      # PathPresentation inyectada por el consumidor (default identidad)
    exec_env: Any = None          # ToolExecEnvironment inyectado por el consumidor (default in-process)
    small_llm: Any = None
    model_id: str = ""
    background_result_max_chars: int = 2000
    # Permisos sembrados en el ctx del agente principal (p.ej. `write_file` para que el
    # modelo pueda guardar memorias). La memoria NO se auto-concede el permiso — es una
    # decisión del integrador, espejo de cómo el canónico permite `Write`.
    initial_allowed_tools: list[str] = field(default_factory=list)
    # Seam de autoría per-request del ctx RAÍZ por el consumidor: `(ctx, task) -> ctx`,
    # aplicado en `_run_loop` solo para el agente principal (parent_snapshot is None).
    # Espeja la autoría per-request del `ToolUseContext` del canónico (canUseTool/
    # handleElicitation/app_state) sobre los puntos de extensión ya existentes
    # (`app_state.native` + `ctx.presentation`), sin replicar su bolsa monolítica. Los
    # subagentes NO lo reciben: su estado viaja por el ForkSnapshot.
    root_context_modifier: Any = None
    # Seam per-request de hooks de inicio de run para el agente RAÍZ:
    # `(task) -> list[Callable[[], Awaitable[None]]]`. `_run_loop` registra los hooks
    # devueltos en el `AgentLoop` de la raíz (`parent_snapshot is None`), que los dispara
    # al arrancar `run()` (turn-start). Espeja el drain de notificaciones background que
    # el canónico hace DENTRO del loop; el consumidor (paquete separado) no puede alcanzar
    # el loop, así que lo inyecta aquí. Devuelve `[]` para sesiones desconocidas.
    root_turn_start_hooks: Any = None


# ---------------------------------------------------------------------------
# RuntimeFactory — meta-factory con extension primitive
# ---------------------------------------------------------------------------

class RuntimeFactory:
    _modes: dict[str, Type] = {}

    @classmethod
    def register_execution_mode(cls, name: str, runtime_cls: Type) -> None:
        cls._modes[name] = name if False else runtime_cls

    @classmethod
    def _build_capability_manager(cls, caps: "CapabilitiesConfig", storage: Any = None) -> Any:
        """Ensambla el CapabilityManager con providers MCP/Skills declarados.

        Registra servers MCP y dirs de skills de forma tolerante (config inválida
        no aborta el ensamblado). Los servers MCP se CONECTAN en `manager.startup()`
        (lo invoca el integrador), no aquí — el factory no abre conexiones de red.
        """
        from .capabilities.manager import CapabilityManager
        from .capabilities.mcp import McpProvider
        from .capabilities.skills import SkillsProvider

        providers: list[Any] = []

        if caps.mcp_servers or caps.mcp_config_store is not None:
            mcp = McpProvider(
                config_store=caps.mcp_config_store,  # registro persistido (lee en startup)
                storage=storage,  # TokenStorage OAuth por defecto sobre StorageProtocol
                redirect_handler=caps.mcp_oauth_redirect_handler,
                callback_handler=caps.mcp_oauth_callback_handler,
            )
            if caps.mcp_servers:
                mcp.load_servers(caps.mcp_servers)  # tolerante; conecta en startup()
            providers.append(mcp)

        if caps.skill_dirs or caps.skill_store is not None:
            skills = SkillsProvider(skill_store=caps.skill_store)  # lee el store en startup
            for root in caps.skill_dirs:
                skills.load_dir(root)
            providers.append(skills)

        if caps.memory_store is not None or caps.memory_root is not None:
            from .capabilities.memory import FilesystemMemoryStore, MemoryProvider

            store = caps.memory_store
            if store is None and caps.memory_root is not None:
                store = FilesystemMemoryStore(caps.memory_root)
            providers.append(MemoryProvider(store))

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
        capability_manager = cls._build_capability_manager(config.capabilities, storage=storage)

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

        # Voz: cada canal queda activo sii su primitiva está inyectada y habilitada.
        # El gate vive aquí; el runtime solo recibe la primitiva o None.
        voice = config.voice
        stt = voice.stt if (voice.stt is not None and voice.stt_enabled) else None
        tts = voice.tts if (voice.tts is not None and voice.tts_enabled) else None

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
            initial_allowed_tools=config.initial_allowed_tools,
            root_context_modifier=config.root_context_modifier,
            root_turn_start_hooks=config.root_turn_start_hooks,
            stt=stt,
            tts=tts,
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
