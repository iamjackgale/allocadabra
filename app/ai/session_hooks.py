"""AI-local hooks for storing chat messages in active workflow state."""

from __future__ import annotations

from typing import Any, Literal

from app.storage.schemas import utc_now_iso
from app.storage.session_state import get_workflow_state, save_workflow_state


ChatMode = Literal["configuration", "review"]
ChatRole = Literal["user", "assistant"]


def append_chat_message(
    mode: ChatMode,
    role: ChatRole,
    content: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one chat message and return the saved workflow state."""
    state = get_workflow_state()
    sessions = state.setdefault("chat_sessions", {"configuration": [], "review": []})
    messages = sessions.setdefault(mode, [])
    message: dict[str, Any] = {
        "role": role,
        "content": content,
        "created_at": utc_now_iso(),
    }
    if metadata:
        message["metadata"] = metadata
    messages.append(message)
    return save_workflow_state(state)


def get_chat_messages(mode: ChatMode, *, limit: int | None = None) -> list[dict[str, Any]]:
    """Return stored chat messages for the requested AI mode."""
    state = get_workflow_state()
    messages = state.get("chat_sessions", {}).get(mode, [])
    if not isinstance(messages, list):
        return []
    if limit is None:
        return messages
    return messages[-limit:]
