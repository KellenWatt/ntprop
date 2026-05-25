# NTProp

A simple mechanism for using Network Tables entries as semi-transparent member variables

## Installation

Using your Python package manager of choice, just install the `ntprop` package from PyPI.
```bash
pip install ntprop
```

## Usage

To start using these, you just need to import `NTPropertyHost` from `ntprop` and have 
your class inherit from it. From there, any member varaible that is of the types `NumberProperty`,
`BooleanProperty`, or `StringProperty` (also from `ntprop`) will act like a simple, strictly-typed 
member variable that transparently updates and is updated by the relevant NT entry.

### Example

```python
from ntprop import NTPropertyHost, NumberProperty

class Foo(NTPropertyHost):
    # for purposes of type-checking here, we could just call this a float, since there's no difference in 
    # usage at runtime. This is only valid if the owning class is an NTPropertyHost.
    bar: NumberProperty

    def __init__(self):
        self.bar = NumberProperty("ntbar", default=1, readonly=False) #defaults are 0.0 and False, respectively

    def do_something(self):
        # += may work?
        self.bar = self.bar + 1 
        print(self.bar)
```

It's also possible to use an NTProperty without it being a member of ah `NTPropertyHost`. To do that, you just
need to use the `get` and `set` methods of the type. *NOTE: These methods are not available in `NTPropertyHost`s 
since that type already does the necessary calls to `get` and `set` behind the scenes and resolves them prior to
returning a value.*

### Bindings
It's possible to bind to changes to a property using the `NTProperty.bind` method, and providing a callback 
compatible with `Callable[[Any], None]`. The callback will be called any time the value changes, both from the 
local program and NetworkTables.

To bind a callback for a property in an `NTPropertyHost`, call the `NTPropertyHost.bind` method, passing the 
name of the NT entry with the callback using `kwargs` syntax. If your entry name is incompatible with Python
name syntax, you can use a `dict` with the entry name as the key and the callback as the associated value.
Either argument method allows multiple key-value pairs, so you can bind multiple callbacks at once.

***Note:*** Be aware that local changes may cause the callback to be called multiple times. It is recommended to 
only use idempotent (same every time) callbacks as well as not make them any more expensive to call than 
strictly necessary.

***Warning:*** There is no guarantee of the callback being called in the same thread it was created it (e.g. the NT
listener that does background updates runs in a different non-Python thread), so any interactions with the outside 
world must be thread safe. If you don't know what that means, you're probably fine, and if you do know what it means, 
but not how to fix it, visit [the Python docs on the `threading` module](https://docs.python.org/3/library/threading.html).
