#!/usr/bin/env python3

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import build_package


class PreviewSpecimenTest(unittest.TestCase):
    def test_native_component_specimens_are_rendered(self) -> None:
        skill_dir = Path(__file__).resolve().parent.parent
        token_path = skill_dir / "assets" / "tokens.example.json"

        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            build_package.build(token_path, output_dir, "example-market", False, False)
            preview = (output_dir / "example-market-preview.html").read_text(encoding="utf-8")

        self.assertIn('data-component="button-primary"', preview)
        self.assertIn("<button", preview)
        self.assertIn('role="switch"', preview)
        self.assertIn('type="range"', preview)


if __name__ == "__main__":
    unittest.main()
