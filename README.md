# Revalidate

A package to manage interdependent fields. 


## Installation

Install the package with pip:
```shell
pip install revalidate
```


## What `revalidate` does

Imagine you write a class that represents a system and has two inputs and three outputs.
Users can set any of the input values and query all input and output values. 
Let's assume that the computation of the output values is expensive.
So, we only want to compute an output value if necessary. 
A first approach is to cache the output values. 
But what happens when in input changes?
Do all outputs values need to be recomputed or are some still valid?
The package `revalidate` keeps track of dependencies between values and knows when a value needs to be recomputed (or revalidated).

The class for the `System` could look as follows:

```python
# coding=utf-8

from revalidate import variable, VariableBase, compute

class System(VariableBase):
    input_1: float = variable()
    input_2: float = variable()

    output_1 = variable(depends_on=["input_1", "input_2"], read_only=True)
    output_2 = variable(depends_on=["input_2"], read_only=True)
    output_3 = variable(depends_on=["output_1"], read_only=True)

    def __init__(self, input_1, input_2):
        self.input_1 = input_1
        self.input_2 = input_2

    @compute("output_1")
    def _compute_output_1(self):
        return self.input_1 + self.input_2

    @compute("output_2")
    def _compute_2(self):
        return 2 * self.input_2

    @compute("output_3")
    def _compute_3(self):
        return 2 * self.output_1
```

First, the class `System` must inherit from `VariableBase` in order for the following code to work. 
Then, the input and output variables are defined on the class with the `variable` keyword. 
For each variable, the dependencies are given here. 
This information is used internally to mark variables invalid when one of its dependencies changes. 
For example, if `input_1` changes, `output_1` becomes invalid because it depends on `input_1`.
As a consequence, `output_2` becomes also invalid because it depends on `outpt_1` which just became invalid. 

There is a compute function, marked with the decorator `compute`, defined for all output variables. 
These functions are used to compute the value of a variable from other variables on the object.
They are only called if necessary. 


## Contribution

Clone the repo and run
```shell
uv sync --extra dev
```
to set up the development environment.
