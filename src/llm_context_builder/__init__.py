"""llm-context-builder-py — compose system prompts from named, ordered sections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Section:
    name: str
    content: str
    priority: int = 0
    enabled: bool = True


class ContextBuilder:
    """
    Compose LLM system prompts from named, ordered sections.

    Sections are rendered in descending priority order. Disabled sections
    are skipped. Supports variable interpolation via str.format_map.

    Example::

        builder = ContextBuilder()
        builder.add("role",     "You are a helpful coding assistant.", priority=100)
        builder.add("format",   "Always respond in markdown.", priority=50)
        builder.add("tool_hint","Use tools when needed.", priority=10)

        system_prompt = builder.build()
    """

    def __init__(self, separator: str = "\n\n") -> None:
        self._sections: dict[str, Section] = {}
        self._separator = separator

    def add(
        self,
        name: str,
        content: str,
        priority: int = 0,
        enabled: bool = True,
    ) -> "ContextBuilder":
        """Add or replace a named section."""
        self._sections[name] = Section(
            name=name, content=content, priority=priority, enabled=enabled
        )
        return self

    def update(self, name: str, content: str) -> "ContextBuilder":
        """Update the content of an existing section (keeps priority/enabled)."""
        if name in self._sections:
            self._sections[name].content = content
        else:
            self.add(name, content)
        return self

    def enable(self, name: str) -> "ContextBuilder":
        if name in self._sections:
            self._sections[name].enabled = True
        return self

    def disable(self, name: str) -> "ContextBuilder":
        if name in self._sections:
            self._sections[name].enabled = False
        return self

    def remove(self, name: str) -> "ContextBuilder":
        self._sections.pop(name, None)
        return self

    def has(self, name: str) -> bool:
        return name in self._sections

    def build(self, variables: dict[str, Any] | None = None) -> str:
        """
        Render the system prompt.

        Args:
            variables: Optional dict for str.format_map interpolation.
        """
        active = sorted(
            (s for s in self._sections.values() if s.enabled),
            key=lambda s: -s.priority,
        )
        parts = []
        for s in active:
            content = s.content
            if variables:
                try:
                    content = content.format_map(variables)
                except (KeyError, IndexError, AttributeError, TypeError, ValueError):
                    # Best-effort interpolation: leave content untouched on any
                    # malformed/unsatisfiable placeholder rather than failing build().
                    content = s.content
            parts.append(content.strip())
        return self._separator.join(parts)

    def as_message(self, variables: dict[str, Any] | None = None) -> dict:
        """Return a system message dict ready for the LLM."""
        return {"role": "system", "content": self.build(variables)}

    def section_names(self) -> list[str]:
        return [
            s.name for s in sorted(self._sections.values(), key=lambda s: -s.priority)
        ]

    def clone(self) -> "ContextBuilder":
        """Return a deep copy of this builder."""
        new = ContextBuilder(self._separator)
        for name, sec in self._sections.items():
            new._sections[name] = Section(
                name=sec.name,
                content=sec.content,
                priority=sec.priority,
                enabled=sec.enabled,
            )
        return new


__all__ = ["ContextBuilder", "Section"]
