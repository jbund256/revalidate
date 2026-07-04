# Revalidate

A package to manage interdependent fields. 


## Installation

Install the package with pip:
```shell
pip install revalidate
```

## What `revalidate` does

`revalidate` is useful when some values in a class are derived from other values.
For example, in a shopping cart:

- `price`, `quantity`, and `discount_percent` are user inputs,
- `subtotal`, `discount_amount`, and `total` are derived values.

You only want to recompute derived values when needed, and only if one of their dependencies changed.
That is exactly what `revalidate` handles.

### Define your class

Here's a complete `CartItem` class that uses `revalidate`:

```python
# coding=utf-8
from revalidate import variable, VariableBase, compute

class CartItem(VariableBase):
    # Inputs users can set
    price: float = variable()
    quantity: int = variable()
    discount_percent: float = variable()

    # Derived values with their dependencies
    subtotal = variable(depends_on=["price", "quantity"], read_only=True)
    discount_amount = variable(depends_on=["subtotal", "discount_percent"], read_only=True)
    total = variable(depends_on=["subtotal", "discount_amount"], read_only=True)

    def __init__(self, price: float, quantity: int, discount_percent: float = 0.0):
        self.price = price
        self.quantity = quantity
        self.discount_percent = discount_percent

    @compute("subtotal")
    def _compute_subtotal(self):
        print("Computing subtotal")
        return self.price * self.quantity

    @compute("discount_amount")
    def _compute_discount_amount(self):
        print("Computing discount_amount")
        return self.subtotal * (self.discount_percent / 100.0)

    @compute("total")
    def _compute_total(self):
        print("Computing total")
        return self.subtotal - self.discount_amount
```

`CartItem` inherits from `VariableBase`, and each field is declared with `variable()`.
Dependencies tell `revalidate` what to invalidate when an input changes.
For example, if `discount_percent` changes, `discount_amount` and `total` are invalidated, but `subtotal` remains valid.

### Usage

Here's how it works in practice. First access computes all dependencies:

```python
>>> item = CartItem(price=50.0, quantity=2, discount_percent=10.0)
>>> print(item.total)
Computing total
Computing subtotal
Computing discount_amount
90.0
```

Access the value again—no recomputation, everything is cached:

```python
>>> print(item.total)
90.0
```

Change only the discount. Only `discount_amount` and `total` are recomputed. `subtotal` is unaffected:

```python
>>> item.discount_percent = 20.0
>>> print(item.total)
Computing total
Computing discount_amount
80.0
```

Change the price. This invalidates `subtotal`, which cascades to all dependent values:

```python
>>> item.price = 60.0
>>> print(item.total)
Computing total
Computing subtotal
Computing discount_amount
96.0
```

## Further reading

See the [Github repo](https://github.com/jbund256/revalidate) for further information.
