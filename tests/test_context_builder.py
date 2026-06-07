"""Tests for llm-context-builder-py."""

from llm_context_builder import ContextBuilder, Section


def test_basic_build():
    b = ContextBuilder()
    b.add("role", "You are a helpful assistant.", priority=100)
    b.add("format", "Respond in markdown.", priority=50)
    result = b.build()
    assert "You are a helpful assistant." in result
    assert "Respond in markdown." in result


def test_priority_ordering():
    b = ContextBuilder()
    b.add("low", "LOW", priority=0)
    b.add("high", "HIGH", priority=100)
    b.add("mid", "MID", priority=50)
    result = b.build()
    assert result.index("HIGH") < result.index("MID") < result.index("LOW")


def test_disabled_section_excluded():
    b = ContextBuilder()
    b.add("visible", "VISIBLE", priority=10)
    b.add("hidden", "HIDDEN", priority=5, enabled=False)
    result = b.build()
    assert "VISIBLE" in result
    assert "HIDDEN" not in result


def test_enable_disable():
    b = ContextBuilder()
    b.add("sec", "SECTION", priority=0)
    b.disable("sec")
    assert "SECTION" not in b.build()
    b.enable("sec")
    assert "SECTION" in b.build()


def test_update_existing():
    b = ContextBuilder()
    b.add("role", "Original", priority=10)
    b.update("role", "Updated")
    result = b.build()
    assert "Updated" in result
    assert "Original" not in result


def test_update_nonexistent_adds():
    b = ContextBuilder()
    b.update("new", "New content")
    assert "New content" in b.build()


def test_remove_section():
    b = ContextBuilder()
    b.add("a", "AAA", priority=10)
    b.add("b", "BBB", priority=5)
    b.remove("a")
    result = b.build()
    assert "AAA" not in result
    assert "BBB" in result


def test_has():
    b = ContextBuilder()
    b.add("x", "X")
    assert b.has("x") is True
    assert b.has("y") is False


def test_variable_interpolation():
    b = ContextBuilder()
    b.add("greeting", "Hello, {name}!", priority=10)
    result = b.build(variables={"name": "World"})
    assert result == "Hello, World!"


def test_missing_variable_passthrough():
    b = ContextBuilder()
    b.add("tmpl", "Hi {missing_key}!", priority=10)
    result = b.build(variables={"other": "x"})
    assert "{missing_key}" in result


def test_custom_separator():
    b = ContextBuilder(separator="---")
    b.add("a", "AAA", priority=10)
    b.add("b", "BBB", priority=5)
    result = b.build()
    assert result == "AAA---BBB"


def test_as_message():
    b = ContextBuilder()
    b.add("role", "You are an AI.", priority=10)
    msg = b.as_message()
    assert msg["role"] == "system"
    assert "You are an AI." in msg["content"]


def test_section_names_ordered():
    b = ContextBuilder()
    b.add("c", "C", priority=1)
    b.add("a", "A", priority=100)
    b.add("b", "B", priority=50)
    names = b.section_names()
    assert names == ["a", "b", "c"]


def test_clone_independence():
    b = ContextBuilder()
    b.add("x", "original", priority=10)
    c = b.clone()
    c.update("x", "modified")
    assert "original" in b.build()
    assert "modified" in c.build()


def test_chaining():
    b = ContextBuilder()
    result = (
        b.add("a", "A", priority=10).add("b", "B", priority=5).disable("b").enable("b")
    )
    assert result is b
    assert "A" in b.build()
    assert "B" in b.build()


def test_empty_build():
    b = ContextBuilder()
    assert b.build() == ""


def test_strip_whitespace_from_content():
    b = ContextBuilder()
    b.add("padded", "  Hello World  ", priority=10)
    assert b.build() == "Hello World"


def test_section_dataclass_defaults():
    s = Section(name="role", content="hi")
    assert s.priority == 0
    assert s.enabled is True


def test_empty_variables_dict_is_noop():
    b = ContextBuilder()
    b.add("tmpl", "Hello {name}", priority=10)
    # An empty dict must not attempt interpolation and must not crash.
    assert b.build(variables={}) == "Hello {name}"


def test_interpolation_index_error_passthrough():
    b = ContextBuilder()
    b.add("tmpl", "Item: {items[5]}", priority=10)
    # Out-of-range index on a present key must not crash build().
    assert b.build(variables={"items": [1, 2]}) == "Item: {items[5]}"


def test_interpolation_attribute_error_passthrough():
    b = ContextBuilder()
    b.add("tmpl", "Name: {user.missing}", priority=10)
    # Missing attribute on a present key must not crash build().
    assert b.build(variables={"user": object()}) == "Name: {user.missing}"


def test_interpolation_type_error_passthrough():
    b = ContextBuilder()
    b.add("tmpl", "Val: {n:d}", priority=10)
    # Bad format spec for the supplied value must not crash build().
    assert b.build(variables={"n": "not-an-int"}) == "Val: {n:d}"


def test_one_bad_section_does_not_break_others():
    b = ContextBuilder()
    b.add("good", "Hello, {name}!", priority=20)
    b.add("bad", "Broken: {missing[0]}", priority=10)
    result = b.build(variables={"name": "Alice", "missing": []})
    assert "Hello, Alice!" in result
    assert "Broken: {missing[0]}" in result
