import io
import sys
import types
import unittest
from pathlib import Path
from contextlib import redirect_stdout

# Ensure project root is on sys.path for imports.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.main as main  # type: ignore
from app.co_occurrence_store import CoOccurrenceStore  # type: ignore


class MainCLITests(unittest.TestCase):
    def setUp(self) -> None:
        # Build a tiny deterministic store for tests.
        store = CoOccurrenceStore()
        store.add_transaction(["a", "b", "c"])
        store.add_transaction(["a", "b"])
        store.add_transaction(["b", "c"])
        self.store = store

    def _run_with_commands(self, commands, monkeypatch_store=True, monkeypatch_visualize=True):
        buf = io.StringIO()
        original_load = main.load_store
        original_visualize = main.visualize_interactive
        try:
            if monkeypatch_store:
                main.load_store = lambda path: self.store  # type: ignore
            if monkeypatch_visualize:
                main.visualize_interactive = lambda: None  # type: ignore
            with redirect_stdout(buf):
                main.run_loop(commands)
        finally:
            main.load_store = original_load
            main.visualize_interactive = original_visualize
        return buf.getvalue()

    def test_help_and_quit(self) -> None:
        output = self._run_with_commands(["help", "quit"], monkeypatch_store=False)
        self.assertIn("Supermarket co-occurrence CLI", output)
        self.assertIn("List commands", output)
        self.assertIn("Goodbye!", output)

    def test_stats_and_top_commands(self) -> None:
        output = self._run_with_commands(
            ["load", "stats", "top_pairs 2", "top_with a 2", "count a b", "quit"]
        )
        self.assertIn("Loaded store", output)
        self.assertIn("Items: 3", output)
        self.assertIn("Pairs: 3", output)
        self.assertIn("Item A", output)
        self.assertIn("Items bought with 'a'", output)
        self.assertIn("'a' with 'b':", output)

    def test_unknown_command(self) -> None:
        output = self._run_with_commands(["bogus", "quit"])
        self.assertIn("Unknown command", output)

    def test_visualize_command_calls_hook(self) -> None:
        called = {}

        def fake_visualize():
            called["ran"] = True

        original_visualize = main.visualize_interactive
        try:
            main.visualize_interactive = fake_visualize  # type: ignore
            output = self._run_with_commands(
                ["visualize", "quit"],
                monkeypatch_store=False,
                monkeypatch_visualize=False,
            )
        finally:
            main.visualize_interactive = original_visualize

        self.assertIn("Goodbye!", output)
        self.assertTrue(called.get("ran", False))


if __name__ == "__main__":
    unittest.main()
