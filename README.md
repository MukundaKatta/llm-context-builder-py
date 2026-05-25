# llm-context-builder-py

Compose LLM system prompts from named, prioritized sections. Supports variable interpolation and enable/disable toggles.

## Install

```bash
pip install llm-context-builder-py
```

## Usage

```python
from llm_context_builder import ContextBuilder

builder = ContextBuilder()
builder.add("role",      "You are a helpful coding assistant.", priority=100)
builder.add("format",   "Always respond in markdown.", priority=50)
builder.add("tool_hint","Use tools when needed.", priority=10)

system_prompt = builder.build()

# As a message dict
msg = builder.as_message()   # {"role": "system", "content": "..."}

# Variable interpolation
builder.add("greeting", "Hello, {user_name}!", priority=20)
prompt = builder.build(variables={"user_name": "Alice"})

# Dynamic control
builder.disable("tool_hint")
builder.enable("tool_hint")
builder.update("role", "You are a strict code reviewer.")
builder.remove("format")

# Clone for per-request variants
variant = builder.clone()
variant.add("extra", "Be concise.", priority=5)
```

## API

- `.add(name, content, priority, enabled)` — add or replace section
- `.update(name, content)` — update content, keep priority/enabled
- `.enable(name)` / `.disable(name)` / `.remove(name)`
- `.build(variables)` — render sorted active sections
- `.as_message(variables)` — `{"role":"system","content":"..."}`
- `.clone()` — deep copy
- `.section_names()` — names in priority order

## License

MIT
