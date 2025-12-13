# How to configure namespaces for forward reference resolution

This guide shows you how to control namespace behavior when inspecting types with forward references. By the end, you'll know how to use automatic namespace detection, provide explicit namespaces when needed, and troubleshoot common resolution failures.

## Prerequisites

Before starting:

- Familiarity with Python's `from __future__ import annotations` ([PEP 563](https://peps.python.org/pep-0563/))
- Basic understanding of forward references and why they require namespace context

## Use automatic namespace detection

typing-graph automatically extracts namespaces from the objects you inspect. For most code using PEP 563's stringified annotations, you don't need any configuration.

1. Define your types normally with the future import:

   ```python
   from __future__ import annotations
   from dataclasses import dataclass
   ```

2. Inspect them directly:

   ```python
   # snippet - conceptual example showing auto-resolution
   from typing_graph import inspect_dataclass

   @dataclass
   class Order:
       customer: Customer
       total: float

   @dataclass
   class Customer:
       name: str

   # Forward references resolve automatically
   node = inspect_dataclass(Order)
   customer_field = node.fields[0]
   print(customer_field.type)  # ConcreteNode for Customer class
   ```

   Auto-detection extracts the module's global namespace and adds the class itself for self-references.

!!! tip
    Start with the default behavior. Only add explicit namespace configuration when auto-detection proves insufficient.

## Turn off automatic namespace detection

When you need complete control over namespaces, turn off auto-detection by setting `auto_namespace=False`.

1. Create a config with auto-detection off:

   ```python
   from typing_graph import InspectConfig

   config = InspectConfig(auto_namespace=False)
   ```

2. Provide namespaces explicitly:

   ```python
   from __future__ import annotations
   from dataclasses import dataclass
   from typing_graph import inspect_dataclass, InspectConfig

   @dataclass
   class Order:
       customer: Customer

   @dataclass
   class Customer:
       name: str

   config = InspectConfig(
       auto_namespace=False,
       globalns={"Customer": Customer},
   )
   node = inspect_dataclass(Order, config=config)
   ```

   With `auto_namespace=False`, only the names you provide in `globalns` and `localns` are available for resolution.

Use this approach when:

- You need deterministic, reproducible resolution behavior
- Auto-detected namespaces include names you want to exclude
- You're testing namespace-related edge cases

## Provide context for `inspect_type()`

The `inspect_type()` function operates on raw type annotations. Since annotations don't carry their own namespace context, use the `source` parameter to provide one.

1. Identify a context object (class, function, or module) that contains the namespace you need:

   ```python
   from __future__ import annotations

   class Container:
       items: list[Item]

   class Item:
       name: str
   ```

2. Pass it as `source`:

   ```python
   from typing_graph import inspect_type

   # Without source, "Item" can't be resolved
   node = inspect_type("list[Item]")  # ForwardRefNode (unresolved)

   # With source, namespaces are extracted from the class
   node = inspect_type("list[Item]", source=Container)
   print(type(node).__name__)  # SubscriptedGenericNode
   ```

The `source` parameter accepts:

- **Classes**: extracts module namespace plus the class itself
- **Functions**: extracts `__globals__` plus the owning class for methods
- **Modules**: extracts the module's `__dict__`

!!! note "Cache behavior"
    When you provide a `source` parameter, typing-graph bypasses the global cache. This ensures namespace-dependent results aren't incorrectly reused across different contexts.

## Augment auto-detected namespaces

When auto-detection finds most names but misses a few, augment rather than replace the auto-detected namespaces.

1. Add extra names in `globalns` while leaving `auto_namespace=True`:

   ```python
   # snippet - conceptual example with external module
   from __future__ import annotations
   from dataclasses import dataclass
   from typing_graph import inspect_dataclass, InspectConfig
   from external_module import ExternalType

   @dataclass
   class Model:
       external: ExternalType  # Defined in another module

   # Auto-detection finds module-level names;
   # add ExternalType explicitly
   config = InspectConfig(globalns={"ExternalType": ExternalType})
   node = inspect_dataclass(Model, config=config)
   ```

2. User-provided values take precedence over auto-detected ones:

   ```python
   # snippet - demonstrating precedence
   class Original:
       pass

   class Replacement:
       pass

   # If auto-detection finds "Original", this overrides it
   config = InspectConfig(globalns={"Original": Replacement})
   ```

This design lets you fix specific missing names without losing the benefit of auto-detection for everything else.

## Handle `TYPE_CHECKING` imports

Imports inside `if TYPE_CHECKING:` blocks exist only for static analysis, not at runtime. Auto-detection can't find them.

1. Identify the types imported under `TYPE_CHECKING`:

   ```python
   # snippet - conceptual TYPE_CHECKING pattern
   from __future__ import annotations
   from typing import TYPE_CHECKING
   from dataclasses import dataclass

   if TYPE_CHECKING:
       from heavy_module import HeavyType  # Not available at runtime

   @dataclass
   class Model:
       field: HeavyType
   ```

2. Import them at runtime and provide them explicitly:

   ```python
   # snippet - conceptual example with TYPE_CHECKING import
   from typing_graph import inspect_dataclass, InspectConfig
   from heavy_module import HeavyType  # Import at runtime too

   config = InspectConfig(globalns={"HeavyType": HeavyType})
   node = inspect_dataclass(Model, config=config)
   ```

   If importing the module has side effects or performance costs you want to avoid, you'll need to either accept unresolved forward references or restructure your imports.

## Configure namespace behavior for functions

Function inspection extracts namespaces from the function's `__globals__`. For methods, typing-graph also attempts to resolve the owning class.

1. Inspect a function with forward references:

   ```python
   from __future__ import annotations
   from typing_graph import inspect_function

   class Processor:
       def process(self, data: DataType) -> Result:
           pass

   class DataType:
       value: int

   class Result:
       status: str

   # Auto-detection extracts __globals__ and adds Processor to localns
   node = inspect_function(Processor.process)
   ```

2. For standalone functions, the module's globals are extracted:

   ```python
   from __future__ import annotations
   from typing_graph import inspect_function

   def transform(input: InputType) -> OutputType:
       pass

   class InputType:
       pass

   class OutputType:
       pass

   node = inspect_function(transform)
   # InputType and OutputType resolve via the module's namespace
   ```

!!! note "Method resolution"
    For methods, typing-graph parses `__qualname__` to find the owning class. This works for most cases but may fail for nested classes with complex qualified names or dynamically created methods. In those cases, provide explicit namespaces.

## Configure namespace behavior for modules

When inspecting types defined in a module, you can pass the module as a `source`:

```python
# snippet - conceptual example with module source
from typing_graph import inspect_type
import mymodule

# Use the module's namespace for resolution
node = inspect_type("SomeType", source=mymodule)
```

For modules, auto-detection extracts the module's `__dict__` as the global namespace. The local namespace is empty.

## Troubleshoot common issues

### Forward reference won't resolve

**Symptom**: you get a `ForwardRefNode` with `RefFailed` state instead of the resolved type.

**Check**:

1. Is the type available at runtime? `TYPE_CHECKING` imports aren't.
2. Is the type in scope? Cross-module references need explicit configuration.
3. Is there a typo in the forward reference string?

```python
from typing_graph import inspect_type, ForwardRefNode, RefFailed

node = inspect_type("NonexistentType")
if isinstance(node, ForwardRefNode) and isinstance(node.state, RefFailed):
    print(f"Failed: {node.state.error}")
```

**Fix**: add the missing type to `globalns`:

```python
# snippet - fix for missing types
config = InspectConfig(globalns={"MissingType": ActualType})
```

### Self-references don't resolve

**Symptom**: a class referring to itself (like `TreeNode` with `children: list[TreeNode]`) doesn't resolve.

**Check**: are you using `inspect_type()` with a bare annotation instead of `inspect_dataclass()`?

```python
from __future__ import annotations
from dataclasses import dataclass
from typing_graph import inspect_type

@dataclass
class TreeNode:
    children: list[TreeNode]

# This won't resolve TreeNode because there's no context
node = inspect_type("list[TreeNode]")  # Unresolved
```

**Fix**: either use a class inspection function or provide `source`:

```python
# Option 1: Use inspect_dataclass
node = inspect_dataclass(TreeNode)  # TreeNode resolves

# Option 2: Provide source
node = inspect_type("list[TreeNode]", source=TreeNode)
```

### Type parameters fail to resolve (PEP 695)

**Symptom**: generic types defined with PEP 695 syntax (Python 3.12+) have unresolved type parameters.

**Check**: type parameters from `__type_params__` are added to the local namespace automatically. If they're not resolving:

1. Verify you're on Python 3.12+
2. Check that the type actually uses PEP 695 syntax (`class Foo[T]:` rather than `class Foo(Generic[T]):`)

```python
# snippet - PEP 695 syntax (Python 3.12+)
class Container[T]:
    items: list[T]
```

**Fix**: auto-detection handles this. If it's not working, ensure you're inspecting the class directly:

```python
# snippet - inspecting PEP 695 generic class
from typing_graph import inspect_dataclass

node = inspect_dataclass(Container)
# T is available in the local namespace
```

### Circular imports cause resolution failures

**Symptom**: forward references fail because the target type's module imports this module, creating a cycle.

**Check**: the import system handles most circular imports, but resolution can fail if the type isn't yet defined when the annotation is evaluated.

**Fix**: use string annotations (which PEP 563 provides automatically) and ensure the types exist by the time you inspect:

```python
from __future__ import annotations

# Both modules use stringified annotations;
# inspection happens after both are fully loaded
```

### Unexpected type in resolved reference

**Symptom**: a forward reference resolves to the wrong type.

**Check**: user-provided namespaces take precedence over auto-detected ones. If you're providing `globalns`, verify you haven't accidentally shadowed a name.

```python
# snippet - debugging namespace precedence
config = InspectConfig(globalns={"Order": WrongOrder})  # This shadows the real Order
```

**Fix**: remove the conflicting entry from your explicit namespace, or set `auto_namespace=False` and provide only the names you want.

## Result

You now know how to:

- Use automatic namespace detection for zero-configuration forward reference resolution
- Disable auto-detection when you need explicit control
- Provide context for `inspect_type()` using the `source` parameter
- Augment auto-detected namespaces with extra types
- Handle `TYPE_CHECKING` imports and other edge cases
- Troubleshoot common resolution failures

## See also

- [Forward references](../explanation/forward-references.md) - Deep dive into evaluation modes and the forward reference lifecycle
- [Configuration options](configuration.md) - Full details on `EvalMode` and other configuration
- [`InspectConfig`][typing_graph.InspectConfig] - Configuration class reference
- [`inspect_type()`][typing_graph.inspect_type] - Type inspection function reference
