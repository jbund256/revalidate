---
icon: lucide/rocket
---

# Quick Start

The following minimal example shows how inputs and derived values work together.
For example, in a shopping cart:

- `price`, `quantity`, and `discount_percent` are user inputs,
- `subtotal`, `discount_amount`, and `total` are derived values.

The connection between inputs (rounded corners) and outputs (sharp corners) is also visualized in the following graph:

``` mermaid
graph LR
    price(price) --> subtotal
    quantity(quantity) --> subtotal
    subtotal --> discount_amount
    subtotal --> total
    discount_percent(discount_percent) --> discount_amount
    discount_amount --> total
```

You only want to recompute derived values when needed, and only if one of their dependencies changed.
That is exactly what `revalidate` handles.


## Define your class

Every class that uses `revalidate` must inherit from `VariableBase`.
Each field is declared with `variable()`. The `depends_on` parameter tells `revalidate` which inputs a derived value depends on.

```python
from revalidate import variable, VariableBase, compute

class CartItem(VariableBase): # (1)!
    # Inputs users can set
    price: float = variable() # (2)!
    quantity: int = variable()
    discount_percent: float = variable()

    # Derived values with their dependencies
    subtotal = variable(depends_on=["price", "quantity"], read_only=True) # (3)!
    discount_amount = variable(depends_on=["subtotal", "discount_percent"], read_only=True)
    total = variable(depends_on=["subtotal", "discount_amount"], read_only=True)

    def __init__(self, price: float, quantity: int, discount_percent: float = 0.0): # (4)!
        self.price = price
        self.quantity = quantity
        self.discount_percent = discount_percent

    @compute("subtotal") # (5)!
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

1. The class must inherit from `VariableBase` in order to work.
2. The inputs are set as variables.
3. `read_only=True` prevents the variable from being set manually. Derived values are usually read-only.
4. Initialization of the input values is optional but makes the usage more convenient. 
5. The `@compute("field_name")` decorator marks a method as the computation function for that variable. 
It is called automatically when the variable is accessed and its value is **invalid**.


## Usage

Here's how it works in practice. First access computes all dependencies:

```python
>>> item = CartItem(price=50.0, quantity=2, discount_percent=10.0)
>>> print(item.total)
Computing total
Computing subtotal
Computing discount_amount
90.0
```

Access the value again — no recomputation, everything is cached:

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

This was a simple usage example on how to use `revalidate`.
See [Advanced concepts](advanced.md) for more insights.
