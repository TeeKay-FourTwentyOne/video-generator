"""Offline regression: return-shot context must not weaken adjacent-cut checks."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("anchor_drift", Path(__file__).with_name("anchor-drift.py"))
drift = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drift)


class AnchorContextTest(unittest.TestCase):
    def test_return_requires_explicit_elapsed_action(self):
        with self.assertRaisesRegex(ValueError, "requires --elapsed-action"):
            drift.build_prompt("return-shot", "rails and shutters", "woman looks up")
        prompt = drift.build_prompt("return-shot", "rails and shutters", "woman looks up",
            "A sheet escaped while the camera followed it.", "before", "after")
        self.assertIn("A sheet escaped while the camera followed it.", prompt)
        self.assertIn("IMAGE 1: before", prompt)
        self.assertIn("Do not invent elapsed actions", prompt)
        self.assertNotIn("everything must match", prompt)

    def test_adjacent_modes_remain_strict(self):
        self.assertIn("a hard cut is INSTANTANEOUS", drift.build_prompt("across-cut", "props", "hand"))
        self.assertIn("Veo will interpolate", drift.build_prompt("within-clip", "props", "hand"))
        for mode in ["across-cut", "within-clip"]:
            with self.assertRaisesRegex(ValueError, "requires --mode=return-shot"):
                drift.build_prompt(mode, "props", "hand", "elapsed action")
        with self.assertRaisesRegex(ValueError, "Unknown"):
            drift.build_prompt("unknown", "props", "hand")


if __name__ == "__main__":
    unittest.main()
