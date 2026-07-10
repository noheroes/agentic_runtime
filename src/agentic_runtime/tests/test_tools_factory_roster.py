"""create_tools expone el roster nativo, incluyendo clone_repository."""
from agentic_runtime.tools.factory import create_tools


def test_clone_repository_in_default_native_roster():
    names = {t.name for t in create_tools().all_tools()}
    assert "clone_repository" in names
    # guarda de que sigue siendo un roster nativo real, no solo la nueva tool
    assert {"bash", "read_file", "write_file", "ToolSearch"} <= names


def test_resolve_clone_repository():
    tool = create_tools().resolve("clone_repository")
    assert tool is not None and tool.name == "clone_repository"
