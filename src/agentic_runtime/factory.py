from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

from .capabilities.resolver import CapabilitiesResolver
from .context.presentation import IdentityPresentation
from .context.window import ContextBudget
from .contracts.identity import Scope, SessionRepo
from .models.protocol import ModelOptions
from .storage.factory import StorageRegistry
from .tools.dispatcher import ToolDispatcher
from .tools.exec_env import LocalExecEnvironment
from .tools.factory import create_tools
from .tools.protocol import ToolProtocol


@dataclass
class StorageConfig:
    backend: str = "filesystem"
    root: Path | None = None
    extra_kwargs: dict[str, Any] = field(default_factory=dict)
    instance: Any = None


@dataclass
class ToolsConfig:
    extras: list[ToolProtocol] = field(default_factory=list)
    interactive: bool = False


@dataclass
class CapabilitiesConfig:
    skill_catalog: Any = None
    resolve_timeout_seconds: float = 5.0
    mcp_servers: dict[str, dict[str, Any]] = field(default_factory=dict)
    skill_dirs: list[Path] = field(default_factory=list)
    extra_providers: list[Any] = field(default_factory=list)
    mcp_config_store: Any = None
    mcp_config_watcher: Any = None
    skill_store: Any = None
    memory_root: Path | None = None
    memory_store: Any = None
    mcp_oauth_redirect_handler: Any = None
    mcp_oauth_callback_handler: Any = None


@dataclass
class VoiceConfig:
    stt: Any = None
    tts: Any = None
    stt_enabled: bool = True
    tts_enabled: bool = True


@dataclass
class RuntimeConfig:
    storage: StorageConfig = field(default_factory=StorageConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    capabilities: CapabilitiesConfig = field(default_factory=CapabilitiesConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    model_options: ModelOptions = field(default_factory=ModelOptions)
    input_processor: Any = None
    model_caller: Any = None
    hook_runner: Any = None
    task_registry: Any = None
    subagent_runner_factory: Any = None
    notification_sink: Any = None
    presentation: Any = None
    exec_env: Any = None
    fs: Any = None
    storage_contract: Any = None
    git_credentials: Any = None
    small_llm: Any = None
    model_id: str = ""
    background_result_max_chars: int = 2000
    initial_allowed_tools: list[str] = field(default_factory=list)
    root_context_modifier: Any = None
    root_turn_start_hooks: Any = None
    agent_resolver: Any = None
    scope: Scope | None = None
    session_repo: SessionRepo[Any] | None = None
    context_budget: ContextBudget | None = None


class RuntimeFactory:
    _modes: ClassVar[dict[str, type[Any]]] = {}

    @classmethod
    def register_execution_mode(cls, name: str, runtime_cls: type[Any]) -> None:
        cls._modes[name] = runtime_cls

    @classmethod
    def _build_capability_manager(
        cls, caps: CapabilitiesConfig, storage: Any = None, scope: Scope | None = None
    ) -> Any:
        from .capabilities.manager import CapabilityManager
        from .capabilities.mcp import McpProvider
        from .capabilities.plan import PlanModeProvider
        from .capabilities.skills import SkillsProvider

        providers: list[Any] = [PlanModeProvider()]

        if caps.mcp_servers or caps.mcp_config_store is not None:
            mcp = McpProvider(
                config_store=caps.mcp_config_store,
                config_watcher=caps.mcp_config_watcher,
                storage=storage,
                redirect_handler=caps.mcp_oauth_redirect_handler,
                callback_handler=caps.mcp_oauth_callback_handler,
                scope=scope,
            )
            if caps.mcp_servers:
                mcp.load_servers(caps.mcp_servers)
            providers.append(mcp)

        if caps.skill_dirs or caps.skill_store is not None:
            skills = SkillsProvider(skill_store=caps.skill_store)
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

    @staticmethod
    def _default_subagent_runner_factory(runtime: Any) -> Any:
        from .execution.runner import LocalSubagentRunner

        return LocalSubagentRunner(build_child=lambda _spec: runtime)

    @classmethod
    def _build_local(cls, config: RuntimeConfig) -> Any:
        from .execution.local import LocalAgentRuntime

        if config.storage.instance is not None:
            storage = config.storage.instance
            owns_storage = False
        else:
            storage_kwargs: dict[str, Any] = {}
            if config.storage.root is not None:
                storage_kwargs["root"] = config.storage.root
            storage_kwargs.update(config.storage.extra_kwargs)
            storage = StorageRegistry.create(config.storage.backend, **storage_kwargs)
            owns_storage = True

        tool_registry = create_tools(
            extras=config.tools.extras, interactive=config.tools.interactive
        )

        capability_manager = cls._build_capability_manager(
            config.capabilities, storage=storage, scope=config.scope
        )

        capabilities_resolver = CapabilitiesResolver(
            tool_registry=tool_registry,
            skill_catalog=config.capabilities.skill_catalog,
            resolve_timeout_seconds=config.capabilities.resolve_timeout_seconds,
        )

        tool_dispatcher = ToolDispatcher()

        presentation = config.presentation or IdentityPresentation()

        exec_env = config.exec_env or LocalExecEnvironment()

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
            owns_storage=owns_storage,
            presentation=presentation,
            exec_env=exec_env,
            fs=config.fs,
            storage_contract=config.storage_contract,
            git_credentials=config.git_credentials,
            small_llm=config.small_llm,
            background_result_max_chars=config.background_result_max_chars,
            model_id=config.model_id,
            model_options=config.model_options,
            input_processor=config.input_processor,
            initial_allowed_tools=config.initial_allowed_tools,
            root_context_modifier=config.root_context_modifier,
            root_turn_start_hooks=config.root_turn_start_hooks,
            agent_resolver=config.agent_resolver,
            runner_factory=config.subagent_runner_factory or cls._default_subagent_runner_factory,
            notification_sink=config.notification_sink,
            scope=config.scope,
            session_repo=config.session_repo,
            context_budget=config.context_budget,
            stt=stt,
            tts=tts,
        )


def create_runtime(
    *,
    execution_mode: str = "local",
    config: RuntimeConfig | None = None,
) -> Any:
    if config is None:
        config = RuntimeConfig()

    if execution_mode == "local":
        return RuntimeFactory._build_local(config)

    custom_cls = RuntimeFactory._modes.get(execution_mode)
    if custom_cls is not None:
        return custom_cls(config=config)

    if execution_mode in ("remote", "tmux", "kubernetes", "lambda"):
        raise NotImplementedError(f"execution_mode='{execution_mode}' no implementado aún")

    raise NotImplementedError(f"execution_mode='{execution_mode}' desconocido")
