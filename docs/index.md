---
icon: lucide/refresh-ccw
---

# Revalidate

`revalidate` is a Python package that manages interdependent fields on classes. 
It tracks dependencies between variables, caches resolved values, and invalidates only what is affected after a change.

This is useful when:

- some fields are direct inputs,
- other fields are derived from those inputs,
- computations should run only when they are actually needed.

All managed classes inherit from `VariableBase`, and each managed field is declared with `variable(...)`.

## Where to go next

<div class="grid cards" markdown>

-   :lucide-package-open: **Installation**

    ---

    Get `revalidate` into your project in one command.

    :octicons-arrow-right-24: [Installation](installation.md)

-   :lucide-rocket: **Quick Start**

    ---

    See the shopping-cart example and learn how invalidation works.

    :octicons-arrow-right-24: [Quick Start](quick_start.md)

-   :lucide-zap: **Advanced concepts**

    ---

    Explore every `variable(...)` option and decorator in depth.

    :octicons-arrow-right-24: [Advanced concepts](advanced.md)

-   :octicons-mark-github-16: **GitHub repository**

    ---

    Browse source code, open issues, and contribute.

    :octicons-arrow-right-24: [Github](https://github.com/jbund256/revalidate)

</div>

