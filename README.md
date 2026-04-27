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
