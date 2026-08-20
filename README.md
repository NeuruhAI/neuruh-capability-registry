# Neuruh Capability Registry

A dependency-free typed capability manifest and argument validator for agent runtimes.

The registry declares which operations exist, the arguments they accept, and whether a receipt or precondition is required. Unknown operations and unknown arguments fail closed.

## Install

```bash
git clone https://github.com/NeuruhAI/neuruh-capability-registry.git
cd neuruh-capability-registry
python -m venv .venv
source .venv/bin/activate
pip install .
```

Or install a pinned release directly:

```bash
pip install "neuruh-capability-registry @ git+https://github.com/NeuruhAI/neuruh-capability-registry.git@v0.1.2-alpha"
```

## Example

```python
import json
from pathlib import Path

from neuruh_capability_registry import CapabilityRegistry

manifest = json.loads(
    Path("examples/capabilities.synthetic.json").read_text()
)
registry = CapabilityRegistry.from_manifest(manifest)

registry.validate_args(
    "document.render",
    {"format": "html", "sections": ["Summary", "Evidence"]},
)
print(registry.list())
```

Expected output:

```text
('document.render',)
```

`validate_args` rejects missing required arguments, unsupported argument types, unknown fields, values outside an enum, and configured length or item-count limits. Every rejection raises `CapabilityError` with a stable code.

The installed CLI validates a manifest, and optionally one operation payload against it:

```bash
neuruh-capability-registry examples/capabilities.synthetic.json

neuruh-capability-registry examples/capabilities.synthetic.json \
  --operation document.render \
  --args '{"format":"html","sections":["Summary","Evidence"]}'
```

Expected output:

```text
VALID 1 capabilities
VALID document.render
```

The CLI exits nonzero and prints the error code when validation fails.

## API

| Name | Purpose |
| --- | --- |
| `CapabilityRegistry.from_manifest(mapping)` | Build a registry from a parsed manifest. |
| `CapabilityRegistry.list()` | Tuple of declared operation names. |
| `CapabilityRegistry.resolve(operation)` | The `Capability`, or `E_CAPABILITY_UNKNOWN`. |
| `CapabilityRegistry.validate_args(operation, args)` | Fail-closed argument validation. |
| `Capability` | `operation`, `kind`, `arg_schema`, `requires_receipt`, `requires_precondition`, `allowed_target_types`. |
| `ArgField` | `type` (`string`, `number`, `boolean`, `string[]`), `required`, `max_length`, `max_items`, `enum`. |
| `CapabilityError(code, message)` | `E_SCHEMA`, `E_SCHEMA_VERSION`, `E_DUPLICATE`, `E_CAPABILITY_UNKNOWN`, `E_ARGUMENTS`. |

## Test

```bash
python -m unittest discover -s tests -v
```

## Safety boundary

The registry answers "is this operation declared, and are these arguments well formed". It does not authorize, execute, or rank anything, and it holds no credentials. A capability passing validation is still subject to whatever policy and execution guard sit downstream.

The example manifest is synthetic and contains no production capability topology. See the [Neuruh Public Commons boundary](https://github.com/NeuruhAI/public-commons/blob/main/PUBLIC_PRIVATE_BOUNDARY.md).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
