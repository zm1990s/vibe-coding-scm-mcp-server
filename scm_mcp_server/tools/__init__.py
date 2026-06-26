"""
Tool 分发入口。
"""
from mcp import types
from scm_mcp_server.tools import readonly as _readonly


def call(name: str, args: dict) -> dict:
    result = _readonly.call(name, args)
    if result is not None:
        return result
    # TODO: write tools (create_*/update_*/delete_*/move_*)
    return {"error": f"Tool not implemented: {name}"}


def list_tool_descriptors() -> list[types.Tool]:
    return _readonly.list_tool_descriptors()
