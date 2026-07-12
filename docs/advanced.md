---
icon: lucide/zap
---

# Advanced concepts

This page documents the full feature set of `revalidate`, grouped by:

- [`variable(...)` options](#features-by-decorators),
- [decorators](#features-by-decorators),
- [additional package concepts](#additional-package-concepts).


## Features by `variable(...)` options

### `depends_on`

Defines upstream dependencies. When one dependency changes, this variable is marked invalid and will be recomputed on next access.

```python
from revalidate import variable, VariableBase, compute


class Rectangle(VariableBase):
    width = variable()
    height = variable()
    area = variable(depends_on=["width", "height"], read_only=True)

    @compute("area")
    def _compute_area(self):
        return self.width * self.height
```

### `invalidates`

Defines downstream invalidation explicitly. When this variable is set, all listed variables become invalid.
This option invalidates in the opposite direction as [`depends_on`](#depends_on).

This is useful for mutually dependent systems where multiple fields can become the source of truth.

```python
import math
from revalidate import variable, VariableBase, compute


class Circle(VariableBase):
    radius = variable(depends_on=["diameter", "area", "circumference"])
    diameter = variable(depends_on=["radius"])
    area = variable(depends_on=["radius"])
    circumference = variable(depends_on=["radius"])

    def __init__(self, radius: float):
        self.radius = radius

    @compute("radius")
    def _compute_radius(self):
        if self._variable_manager.diameter.valid:
            return self.diameter / 2
        if self._variable_manager.area.valid:
            return math.sqrt(self.area / math.pi)
        if self._variable_manager.circumference.valid:
            return self.circumference / (2 * math.pi)

    @compute("diameter")
    def _compute_diameter(self):
        return 2 * self.radius

    @compute("area")
    def _compute_area(self):
        return math.pi * self.radius**2

    @compute("circumference")
    def _compute_circumference(self):
        return 2 * math.pi * self.radius
```

### `default`

Provides a static default value. A variable with a default starts as valid.

```python
from revalidate import variable, VariableBase


class Config(VariableBase):
    timeout = variable(default=30)
```

### `default_factory`

Provides a per-instance factory for defaults (recommended for mutable values). 
A variable with a default starts as valid.

```python
from revalidate import variable, VariableBase


class Config(VariableBase):
    tags = variable(default_factory=list)
```

!!! warning

    Do not combine `default` and `default_factory` on the same variable.

### `read_only`

Makes a variable readable but not directly settable.
Commonly used for derived values.

```python
from revalidate import variable, VariableBase, compute


class Stats(VariableBase):
    values = variable()
    mean = variable(depends_on=["values"], read_only=True)

    @compute("mean")
    def _compute_mean(self):
        return sum(self.values) / len(self.values)
```

A read-only variable must be computable or have a default.

### `write_only`

Makes a variable settable but not readable via normal attribute access.
Useful for sensitive inputs.

```python
from revalidate import variable, VariableBase, compute


class Hasher(VariableBase):
    password = variable(write_only=True)
    token = variable(depends_on=["password"], write_only=True)

    @compute("token")
    def _compute_token(self):
        return hash(self._variable_manager["password"].value)
```

!!! warning

    A variable cannot be both `read_only=True` and `write_only=True`.

### `use_invalid_value`

Controls behaviour when an invalid variable cannot be computed.

- `False` (default): raises `VariableComputationError`
- `True`: returns [`invalid_value`](#invalid_value) instead

```python
from revalidate import variable, VariableBase, compute


class Sensor(VariableBase):
    raw = variable()
    processed = variable(depends_on=["raw"], use_invalid_value=True, invalid_value=float("nan"))

    @compute("processed")
    def _compute_processed(self):
        if self.raw < 0:
            raise ValueError("out of range")
        return self.raw * 2
```

### `invalid_value`

Value returned when `use_invalid_value=True` and computation fails or is not possible.
Defaults to [`INVALID`](#invalid-sentinel).

```python
from revalidate import INVALID, variable, VariableBase


class Fallback(VariableBase):
    x = variable(use_invalid_value=True)

f = Fallback()
assert f.x is INVALID
```

### `doc`

Adds a docstring to the generated Python property.

```python
from revalidate import variable, VariableBase


class Circle(VariableBase):
    radius = variable(doc="Radius in meters")
```

## Features by decorators

### `@compute("name")`

Registers the compute function used when a variable is accessed while invalid.
Computed values are cached and marked valid.

```python
from revalidate import variable, VariableBase, compute


class Sample(VariableBase):
    x = variable()

    @compute("x")
    def _compute_x(self):
        return 42
```

### `@getter("name")`

Registers a getter hook called on every read after value resolution.
Useful for output transformation, formatting, telemetry, or access tracking.

```python
from revalidate import variable, VariableBase, getter


class Temperature(VariableBase):
    celsius = variable(default=21.234)

    @getter("celsius")
    def _get_celsius(self, value):
        return round(value, 1)
```

### `@setter("name")`

Registers a setter hook called on explicit assignment.
Useful for validation and normalization.

```python
from revalidate import variable, VariableBase, setter


class Account(VariableBase):
    balance = variable(default=0)

    @setter("balance")
    def _set_balance(self, value):
        if value < 0:
            raise ValueError("balance must be >= 0")
        return value
```

!!! note

    Setter hooks run on assignment only. They are not called by compute functions.

## Additional package concepts

### `INVALID` sentinel

`INVALID` marks a variable as unresolved.
If a compute function returns `INVALID`, the variable remains invalid and can be retried on next access.

### `VariableBase`

All managed classes must inherit from `VariableBase`.
This enables class-time registration of variable prototypes and instance-time creation of a `VariableManager`.

