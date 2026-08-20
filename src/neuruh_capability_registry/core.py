from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class CapabilityError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ArgField:
    type: str
    required: bool = False
    max_length: int | None = None
    max_items: int | None = None
    enum: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ArgField":
        field_type = str(raw.get("type", ""))
        if field_type not in {"string", "number", "boolean", "string[]"}:
            raise CapabilityError(
                "E_SCHEMA", f"unsupported argument type: {field_type}"
            )
        return cls(
            type=field_type,
            required=bool(raw.get("required", False)),
            max_length=int(raw["max_length"])
            if raw.get("max_length") is not None
            else None,
            max_items=int(raw["max_items"])
            if raw.get("max_items") is not None
            else None,
            enum=tuple(str(x) for x in raw.get("enum", ())),
        )


@dataclass(frozen=True)
class Capability:
    operation: str
    kind: str
    arg_schema: Mapping[str, ArgField]
    requires_receipt: bool = True
    requires_precondition: bool = False
    allowed_target_types: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "Capability":
        operation = str(raw.get("operation", ""))
        kind = str(raw.get("kind", ""))
        if not operation:
            raise CapabilityError("E_SCHEMA", "operation is required")
        if kind not in {"filesystem", "process", "network", "data", "other"}:
            raise CapabilityError("E_SCHEMA", f"unsupported capability kind: {kind}")
        schema_raw = raw.get("arg_schema", {})
        if not isinstance(schema_raw, Mapping):
            raise CapabilityError("E_SCHEMA", "arg_schema must be an object")
        schema = {str(k): ArgField.from_mapping(v) for k, v in schema_raw.items()}
        return cls(
            operation=operation,
            kind=kind,
            arg_schema=schema,
            requires_receipt=bool(raw.get("requires_receipt", True)),
            requires_precondition=bool(raw.get("requires_precondition", False)),
            allowed_target_types=tuple(
                str(x) for x in raw.get("allowed_target_types", ())
            ),
        )


class CapabilityRegistry:
    """Immutable operation registry with exact argument validation."""

    def __init__(self, capabilities: Sequence[Capability]):
        if not capabilities:
            raise CapabilityError("E_SCHEMA", "at least one capability is required")
        by_operation: dict[str, Capability] = {}
        for cap in capabilities:
            if cap.operation in by_operation:
                raise CapabilityError(
                    "E_DUPLICATE", f"duplicate capability: {cap.operation}"
                )
            by_operation[cap.operation] = cap
        self._by_operation = by_operation

    @classmethod
    def from_manifest(cls, manifest: Mapping[str, Any]) -> "CapabilityRegistry":
        if manifest.get("schema_version") != "neuruh.capability-registry.v0.1":
            raise CapabilityError("E_SCHEMA_VERSION", "unsupported schema_version")
        raw_caps = manifest.get("capabilities")
        if not isinstance(raw_caps, list):
            raise CapabilityError("E_SCHEMA", "capabilities must be an array")
        return cls([Capability.from_mapping(c) for c in raw_caps])

    def list(self) -> tuple[str, ...]:
        return tuple(self._by_operation)

    def resolve(self, operation: str) -> Capability:
        try:
            return self._by_operation[operation]
        except KeyError as exc:
            raise CapabilityError(
                "E_CAPABILITY_UNKNOWN", f"unknown capability: {operation}"
            ) from exc

    def validate_args(self, operation: str, args: Mapping[str, Any]) -> None:
        cap = self.resolve(operation)
        if not isinstance(args, Mapping):
            raise CapabilityError("E_ARGUMENTS", "args must be an object")

        unknown = sorted(set(args) - set(cap.arg_schema))
        if unknown:
            raise CapabilityError(
                "E_ARGUMENTS", f"unknown argument(s): {', '.join(unknown)}"
            )

        for name, spec in cap.arg_schema.items():
            if name not in args:
                if spec.required:
                    raise CapabilityError(
                        "E_ARGUMENTS", f"missing required argument: {name}"
                    )
                continue
            value = args[name]
            self._validate_value(name, value, spec)

    @staticmethod
    def _validate_value(name: str, value: Any, spec: ArgField) -> None:
        if spec.type == "string":
            if not isinstance(value, str):
                raise CapabilityError("E_ARGUMENTS", f"{name} must be a string")
            if spec.max_length is not None and len(value) > spec.max_length:
                raise CapabilityError("E_ARGUMENTS", f"{name} exceeds max_length")
            if spec.enum and value not in spec.enum:
                raise CapabilityError("E_ARGUMENTS", f"{name} is not in enum")
        elif spec.type == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise CapabilityError("E_ARGUMENTS", f"{name} must be a number")
        elif spec.type == "boolean":
            if not isinstance(value, bool):
                raise CapabilityError("E_ARGUMENTS", f"{name} must be a boolean")
        elif spec.type == "string[]":
            if not isinstance(value, list) or not all(
                isinstance(x, str) for x in value
            ):
                raise CapabilityError(
                    "E_ARGUMENTS", f"{name} must be an array of strings"
                )
            if spec.max_items is not None and len(value) > spec.max_items:
                raise CapabilityError("E_ARGUMENTS", f"{name} exceeds max_items")
            if spec.max_length is not None and any(
                len(x) > spec.max_length for x in value
            ):
                raise CapabilityError(
                    "E_ARGUMENTS", f"{name} contains an item exceeding max_length"
                )
