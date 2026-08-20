import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from neuruh_capability_registry.cli import main

from test_registry import MANIFEST


class CapabilityRegistryCliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.manifest = Path(self.directory.name) / "capabilities.json"
        self.manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")

    def tearDown(self):
        self.directory.cleanup()

    def test_validates_manifest(self):
        output = StringIO()
        with redirect_stdout(output):
            status = main([str(self.manifest)])

        self.assertEqual(status, 0)
        self.assertEqual(output.getvalue(), "VALID 1 capabilities\n")

    def test_validates_operation_arguments(self):
        output = StringIO()
        with redirect_stdout(output):
            status = main(
                [
                    str(self.manifest),
                    "--operation",
                    "file.write_synthetic",
                    "--args",
                    '{"content":"safe"}',
                ]
            )

        self.assertEqual(status, 0)
        self.assertEqual(output.getvalue(), "VALID file.write_synthetic\n")

    def test_returns_nonzero_for_invalid_arguments(self):
        error = StringIO()
        with redirect_stderr(error):
            status = main(
                [
                    str(self.manifest),
                    "--operation",
                    "file.write_synthetic",
                    "--args",
                    "{}",
                ]
            )

        self.assertEqual(status, 1)
        self.assertIn("missing required argument", error.getvalue())


if __name__ == "__main__":
    unittest.main()
