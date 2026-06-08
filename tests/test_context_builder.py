"""Tests for llm-context-builder-py.

These tests use only the Python standard-library ``unittest`` framework so
they can be run without any third-party dependencies::

    python3 -m unittest discover -s tests

The package lives under ``src/`` (a "src layout"), so the import below is made
to work without installation via the path bootstrap in ``tests/__init__.py``.
"""

import os
import sys
import unittest

# Make the ``src/`` layout importable without an editable install so this suite
# runs with a bare ``python3 -m unittest discover -s tests``.
_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from llm_context_builder import ContextBuilder, Section  # noqa: E402


class BuildTests(unittest.TestCase):
    def test_basic_build(self):
        b = ContextBuilder()
        b.add("role", "You are a helpful assistant.", priority=100)
        b.add("format", "Respond in markdown.", priority=50)
        result = b.build()
        self.assertIn("You are a helpful assistant.", result)
        self.assertIn("Respond in markdown.", result)

    def test_priority_ordering(self):
        b = ContextBuilder()
        b.add("low", "LOW", priority=0)
        b.add("high", "HIGH", priority=100)
        b.add("mid", "MID", priority=50)
        result = b.build()
        self.assertLess(result.index("HIGH"), result.index("MID"))
        self.assertLess(result.index("MID"), result.index("LOW"))

    def test_equal_priority_preserves_insertion_order(self):
        b = ContextBuilder()
        b.add("first", "FIRST", priority=10)
        b.add("second", "SECOND", priority=10)
        result = b.build()
        # sorted() is stable, so equal priorities keep insertion order.
        self.assertLess(result.index("FIRST"), result.index("SECOND"))

    def test_empty_build(self):
        b = ContextBuilder()
        self.assertEqual(b.build(), "")

    def test_strip_whitespace_from_content(self):
        b = ContextBuilder()
        b.add("padded", "  Hello World  ", priority=10)
        self.assertEqual(b.build(), "Hello World")

    def test_custom_separator(self):
        b = ContextBuilder(separator="---")
        b.add("a", "AAA", priority=10)
        b.add("b", "BBB", priority=5)
        self.assertEqual(b.build(), "AAA---BBB")


class SectionControlTests(unittest.TestCase):
    def test_disabled_section_excluded(self):
        b = ContextBuilder()
        b.add("visible", "VISIBLE", priority=10)
        b.add("hidden", "HIDDEN", priority=5, enabled=False)
        result = b.build()
        self.assertIn("VISIBLE", result)
        self.assertNotIn("HIDDEN", result)

    def test_enable_disable(self):
        b = ContextBuilder()
        b.add("sec", "SECTION", priority=0)
        b.disable("sec")
        self.assertNotIn("SECTION", b.build())
        b.enable("sec")
        self.assertIn("SECTION", b.build())

    def test_enable_disable_unknown_is_noop(self):
        b = ContextBuilder()
        # Operating on a missing section must not raise.
        self.assertIs(b.enable("nope"), b)
        self.assertIs(b.disable("nope"), b)
        self.assertEqual(b.build(), "")

    def test_update_existing(self):
        b = ContextBuilder()
        b.add("role", "Original", priority=10)
        b.update("role", "Updated")
        result = b.build()
        self.assertIn("Updated", result)
        self.assertNotIn("Original", result)

    def test_update_preserves_priority_and_enabled(self):
        b = ContextBuilder()
        b.add("role", "Original", priority=99, enabled=True)
        b.add("other", "Other", priority=1)
        b.update("role", "Updated")
        # "role" still outranks "other" -> still rendered first.
        result = b.build()
        self.assertLess(result.index("Updated"), result.index("Other"))

    def test_update_nonexistent_adds(self):
        b = ContextBuilder()
        b.update("new", "New content")
        self.assertIn("New content", b.build())

    def test_remove_section(self):
        b = ContextBuilder()
        b.add("a", "AAA", priority=10)
        b.add("b", "BBB", priority=5)
        b.remove("a")
        result = b.build()
        self.assertNotIn("AAA", result)
        self.assertIn("BBB", result)

    def test_remove_unknown_is_noop(self):
        b = ContextBuilder()
        b.add("a", "AAA")
        b.remove("missing")
        self.assertIn("AAA", b.build())

    def test_has(self):
        b = ContextBuilder()
        b.add("x", "X")
        self.assertTrue(b.has("x"))
        self.assertFalse(b.has("y"))

    def test_add_replaces_existing(self):
        b = ContextBuilder()
        b.add("role", "First", priority=10)
        b.add("role", "Second", priority=20)
        self.assertEqual(b.build(), "Second")


class InterpolationTests(unittest.TestCase):
    def test_variable_interpolation(self):
        b = ContextBuilder()
        b.add("greeting", "Hello, {name}!", priority=10)
        self.assertEqual(b.build(variables={"name": "World"}), "Hello, World!")

    def test_missing_variable_passthrough(self):
        b = ContextBuilder()
        b.add("tmpl", "Hi {missing_key}!", priority=10)
        self.assertIn("{missing_key}", b.build(variables={"other": "x"}))

    def test_empty_variables_dict_is_noop(self):
        b = ContextBuilder()
        b.add("tmpl", "Hello {name}", priority=10)
        # An empty dict must not attempt interpolation and must not crash.
        self.assertEqual(b.build(variables={}), "Hello {name}")

    def test_none_variables_is_noop(self):
        b = ContextBuilder()
        b.add("tmpl", "Hello {name}", priority=10)
        self.assertEqual(b.build(variables=None), "Hello {name}")
        self.assertEqual(b.build(), "Hello {name}")

    def test_interpolation_index_error_passthrough(self):
        b = ContextBuilder()
        b.add("tmpl", "Item: {items[5]}", priority=10)
        # Out-of-range index on a present key must not crash build().
        self.assertEqual(
            b.build(variables={"items": [1, 2]}), "Item: {items[5]}"
        )

    def test_interpolation_attribute_error_passthrough(self):
        b = ContextBuilder()
        b.add("tmpl", "Name: {user.missing}", priority=10)
        # Missing attribute on a present key must not crash build().
        self.assertEqual(
            b.build(variables={"user": object()}), "Name: {user.missing}"
        )

    def test_interpolation_type_error_passthrough(self):
        b = ContextBuilder()
        b.add("tmpl", "Val: {n:d}", priority=10)
        # Bad format spec for the supplied value must not crash build().
        self.assertEqual(
            b.build(variables={"n": "not-an-int"}), "Val: {n:d}"
        )

    def test_one_bad_section_does_not_break_others(self):
        b = ContextBuilder()
        b.add("good", "Hello, {name}!", priority=20)
        b.add("bad", "Broken: {missing[0]}", priority=10)
        result = b.build(variables={"name": "Alice", "missing": []})
        self.assertIn("Hello, Alice!", result)
        self.assertIn("Broken: {missing[0]}", result)

    def test_multiple_variables_in_one_section(self):
        b = ContextBuilder()
        b.add("tmpl", "{a} and {b}", priority=10)
        self.assertEqual(b.build(variables={"a": "X", "b": "Y"}), "X and Y")


class MessageAndIntrospectionTests(unittest.TestCase):
    def test_as_message(self):
        b = ContextBuilder()
        b.add("role", "You are an AI.", priority=10)
        msg = b.as_message()
        self.assertEqual(msg["role"], "system")
        self.assertIn("You are an AI.", msg["content"])

    def test_as_message_passes_variables(self):
        b = ContextBuilder()
        b.add("greeting", "Hi {name}", priority=10)
        msg = b.as_message(variables={"name": "Bob"})
        self.assertEqual(msg["content"], "Hi Bob")

    def test_section_names_ordered(self):
        b = ContextBuilder()
        b.add("c", "C", priority=1)
        b.add("a", "A", priority=100)
        b.add("b", "B", priority=50)
        self.assertEqual(b.section_names(), ["a", "b", "c"])

    def test_section_names_empty(self):
        self.assertEqual(ContextBuilder().section_names(), [])


class CloneTests(unittest.TestCase):
    def test_clone_independence(self):
        b = ContextBuilder()
        b.add("x", "original", priority=10)
        c = b.clone()
        c.update("x", "modified")
        self.assertIn("original", b.build())
        self.assertIn("modified", c.build())

    def test_clone_preserves_separator(self):
        b = ContextBuilder(separator="||")
        b.add("a", "A", priority=10)
        b.add("b", "B", priority=5)
        self.assertEqual(b.clone().build(), "A||B")

    def test_clone_section_mutation_isolated(self):
        b = ContextBuilder()
        b.add("x", "X", priority=10, enabled=True)
        c = b.clone()
        c.disable("x")
        # Disabling in the clone must not affect the original section object.
        self.assertIn("X", b.build())
        self.assertEqual(c.build(), "")


class ChainingTests(unittest.TestCase):
    def test_chaining_returns_self(self):
        b = ContextBuilder()
        result = (
            b.add("a", "A", priority=10)
            .add("b", "B", priority=5)
            .disable("b")
            .enable("b")
        )
        self.assertIs(result, b)
        self.assertIn("A", b.build())
        self.assertIn("B", b.build())

    def test_add_update_remove_return_self(self):
        b = ContextBuilder()
        self.assertIs(b.add("a", "A"), b)
        self.assertIs(b.update("a", "AA"), b)
        self.assertIs(b.remove("a"), b)


class SectionDataclassTests(unittest.TestCase):
    def test_section_dataclass_defaults(self):
        s = Section(name="role", content="hi")
        self.assertEqual(s.priority, 0)
        self.assertTrue(s.enabled)

    def test_section_explicit_fields(self):
        s = Section(name="role", content="hi", priority=42, enabled=False)
        self.assertEqual(s.priority, 42)
        self.assertFalse(s.enabled)


if __name__ == "__main__":
    unittest.main()
