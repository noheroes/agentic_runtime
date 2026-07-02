from __future__ import annotations

from pathlib import Path


from agentic_runtime import (
    AppState,
    CompactionProvider,
    NativeToolRegistry,
    PermissionContext,
    ToolPool,
    ToolUseContext,
    apply_context_modifier_compat,
    assemble_tool_pool,
    sync_session_from_tool_use_context,
    collect_compaction_context,
    tool_use_context_from_session,
)
from agentic_runtime.tools.protocol import ToolCategory, ToolResult


class _FakeTool:
    input_schema: dict = {}
    category = ToolCategory.UTILITY
    requires_permission: bool = False
    safe_for_background: bool = True
    timeout_seconds: float = 30.0

    def __init__(self, name: str) -> None:
        self.name = name
        self.description = f"fake {name}"

    async def execute(self, input: dict, ctx=None) -> ToolResult:
        return ToolResult(tool_name=self.name, output=str(input))


def test_tool_pool_assembly_is_stable_and_native_wins_name_collisions():
    native = [_FakeTool("zeta"), _FakeTool("alpha"), _FakeTool("shared")]
    capability = [_FakeTool("shared"), _FakeTool("beta")]

    tools = assemble_tool_pool(native, capability, PermissionContext())

    assert [tool.name for tool in tools] == ["alpha", "shared", "zeta", "beta"]
    assert tools[1] is native[2]


def test_native_tool_registry_has_no_capability_filtering_behavior():
    registry = NativeToolRegistry()
    registry.register(_FakeTool("alpha"))
    registry.register(_FakeTool("mcp__tool"))

    assert registry.names() == ["alpha", "mcp__tool"]
    assert [tool.name for tool in registry.list_tools()] == ["alpha", "mcp__tool"]
    assert registry.get("alpha").name == "alpha"
    assert registry.unregister_by_prefix("mcp__") == 1
    assert registry.names() == ["alpha"]


def test_tool_pool_respects_deny_rules():
    native = [_FakeTool("alpha")]
    capability = [_FakeTool("beta")]

    tools = assemble_tool_pool(
        native,
        capability,
        PermissionContext(always_deny=["beta"]),
    )

    assert [tool.name for tool in tools] == ["alpha"]


def test_tool_use_context_modifier_updates_permissions_without_session_mutation():
    context = ToolUseContext(
        session_id="s1",
        tool_pool=ToolPool(native_tools=[_FakeTool("read_file")]),
        app_state=AppState(),
    )

    def modifier(ctx: ToolUseContext) -> ToolUseContext:
        return ctx.with_permissions(
            ctx.permission_context.with_command_allow(["drawio__create_drawio_diagram"])
        )

    updated = modifier(context)

    assert context.permission_context.always_allow_command == []
    assert updated.permission_context.always_allow_command == [
        "drawio__create_drawio_diagram"
    ]


def test_runtime_contract_modules_do_not_import_skill_or_mcp_packages():
    runtime_dir = Path(__file__).resolve().parents[1]
    checked = [
        runtime_dir / "context" / "tool_use.py",
        runtime_dir / "contracts" / "permissions.py",
        runtime_dir / "tools" / "pool.py",
    ]

    for path in checked:
        source = path.read_text(encoding="utf-8")
        assert "agent_core.skills" not in source
        assert "agent_core.mcp" not in source
        assert "from ..skills" not in source
        assert "from ..mcp" not in source


def test_session_adapter_builds_tool_use_context_without_provider_state():
    class _Metadata:
        permission_grants = ["read_file"]
        invoked_skills = ["drawio-diagrams"]
        discovered_deferred_tools = ["drawio__create_drawio_diagram"]

    class _Session:
        session_id = "s1"
        turn_count = 3
        metadata = _Metadata()

        def get_messages_for_llm(self):
            return [{"role": "user", "content": "hello"}]

    context = tool_use_context_from_session(
        _Session(),
        tool_pool=ToolPool(native_tools=[_FakeTool("read_file")]),
    )

    assert context.session_id == "s1"
    assert context.turn_count == 3
    assert context.messages == [{"role": "user", "content": "hello"}]
    assert context.permission_context.always_allow_session == ["read_file"]
    assert "skills" not in context.app_state.capabilities
    assert "mcp" not in context.app_state.capabilities


def test_sync_session_from_tool_use_context_updates_legacy_permission_grants():
    class _Metadata:
        permission_grants = []

    class _Session:
        metadata = _Metadata()

    context = ToolUseContext(session_id="s1").with_permissions(
        PermissionContext(always_allow_session=["read_file"])
    )

    sync_session_from_tool_use_context(_Session(), context)

    assert _Session.metadata.permission_grants == ["read_file"]


def test_apply_context_modifier_compat_supports_new_tool_use_context_modifiers():
    class _Metadata:
        permission_grants = []

    class _Session:
        metadata = _Metadata()

    def modifier(ctx: ToolUseContext) -> ToolUseContext:
        return ctx.with_permissions(PermissionContext(always_allow_session=["echo"]))

    context = ToolUseContext(session_id="s1")
    updated = apply_context_modifier_compat(
        modifier,
        session=_Session(),
        context=context,
    )

    assert updated.permission_context.always_allow_session == ["echo"]
    assert _Session.metadata.permission_grants == ["echo"]


def test_apply_context_modifier_compat_supports_legacy_session_modifiers():
    class _Metadata:
        permission_grants = []

    class _Session:
        metadata = _Metadata()

    def legacy_modifier(session):
        session.metadata.permission_grants.append("bash")

    context = ToolUseContext(session_id="s1")
    updated = apply_context_modifier_compat(
        legacy_modifier,
        session=_Session(),
        context=context,
    )

    assert updated is context
    assert _Session.metadata.permission_grants == ["bash"]


# test_gpt54_prepare_turn_builds_request_with_assembled_tools borrado en R0:
# probaba GPT54Runtime (internals de agent_core), no es cobertura del runtime.



def test_compaction_providers_are_collected_in_registration_order():
    class _FirstProvider:
        def compact_context(self, context: ToolUseContext) -> list[dict]:
            return [{"role": "user", "content": f"first:{context.session_id}"}]

    class _SecondProvider:
        def compact_context(self, context: ToolUseContext) -> list[dict]:
            return [{"role": "user", "content": "second"}]

    providers: list[CompactionProvider] = [_FirstProvider(), _SecondProvider()]
    context = ToolUseContext(session_id="s1")

    assert collect_compaction_context(providers, context) == [
        {"role": "user", "content": "first:s1"},
        {"role": "user", "content": "second"},
    ]
