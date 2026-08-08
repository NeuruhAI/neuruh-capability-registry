import unittest

from neuruh_capability_registry import CapabilityError, CapabilityRegistry


MANIFEST = {
    "schema_version": "neuruh.capability-registry.v0.1",
    "capabilities": [
        {
            "operation": "file.write_synthetic",
            "kind": "filesystem",
            "requires_receipt": True,
            "requires_precondition": True,
            "allowed_target_types": ["file"],
            "arg_schema": {
                "content": {"type": "string", "required": True, "max_length": 100},
                "mode": {"type": "string", "required": False, "enum": ["replace", "create"]},
            },
        }
    ],
}


class CapabilityRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = CapabilityRegistry.from_manifest(MANIFEST)

    def test_list_and_resolve(self):
        self.assertEqual(self.registry.list(), ("file.write_synthetic",))
        self.assertTrue(self.registry.resolve("file.write_synthetic").requires_receipt)

    def test_unknown_capability_fails_closed(self):
        with self.assertRaises(CapabilityError) as ctx:
            self.registry.resolve("shell.exec")
        self.assertEqual(ctx.exception.code, "E_CAPABILITY_UNKNOWN")

    def test_required_argument(self):
        with self.assertRaises(CapabilityError):
            self.registry.validate_args("file.write_synthetic", {})

    def test_unknown_argument_rejected(self):
        with self.assertRaises(CapabilityError):
            self.registry.validate_args("file.write_synthetic", {"content": "x", "secret": "y"})

    def test_argument_type_rejected(self):
        with self.assertRaises(CapabilityError):
            self.registry.validate_args("file.write_synthetic", {"content": 42})

    def test_enum_rejected(self):
        with self.assertRaises(CapabilityError):
            self.registry.validate_args("file.write_synthetic", {"content": "x", "mode": "append"})

    def test_valid_arguments(self):
        self.registry.validate_args("file.write_synthetic", {"content": "hello", "mode": "replace"})


if __name__ == "__main__":
    unittest.main()
