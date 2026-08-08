# Neuruh Capability Registry

A fail-closed typed capability manifest and argument validator.

It gives an agent runtime a machine-readable answer to:

- which operations exist;
- what kind of operation each one is;
- which arguments are accepted;
- which arguments are required;
- whether a receipt or precondition is required;
- which target types are admitted.

Unknown operations and unknown arguments fail closed.

## Quick start

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The example manifest under `examples/` is synthetic and contains no production capability topology.

Status: Active Alpha.
