from typing import Any, ClassVar, Optional, Callable
import ntcore

class NTProperty:
    #  nt_instance: ClassVar[Optional[ntcore.NetworkTableInstance]] = None
    nt_instances: ClassVar[dict[str | None, ntcore.NetworkTableInstance]] = {}
    default_server_address: ClassVar[tuple[str, int]] = ("localhost", 0)

    @classmethod
    def set_default_address(cls, address: str, port: int = 0):
        cls.default_server_address = (address, port)

    @classmethod
    def create_instance(cls, name: Optional[str] = None, address: Optional[str] = None, port: Optional[int] = None) -> ntcore.NetworkTableInstance:
        """Attempts to create a new NetworkTables instance with the given address and port (uses the class defaults if not provided),
        then associates that instance with the given name. If an instance is already associated with the name, that is returned instead,
        ignoring the address and port arguments.

        If no name is provided, this will default to the default NetworkTables instance (`NetworkTableInstance.getDefault()`)"""
        if name in cls.nt_instances:
            return cls.nt_instances[name]
        if address is None:
            address = cls.default_server_address[0]
        if port is None:
            port = cls.default_server_address[1]
        if name is None:
            inst = ntcore.NetworkTableInstance.getDefault()
        else:
            inst = ntcore.NetworkTableInstance.create()
        inst.setServer(address, port)
        inst.startClient4("Reflection")
        cls.nt_instances[name] = inst
        return inst


    def __init_subclass__(cls, ty: str, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.ty = ty

    def __init__(self, name: str, default: Any = None, readonly: bool = False, persistent: bool = False, **kwargs):
        """Additional arguments can be provided as kwargs to control which instance the property connects to. See the
        `NTProperty.create_instance` class method for usable arguments and their meaning."""
        self.bindings = []
        self.path = name
        self.readonly = readonly
        self._update(default, remote=False)
        self.instance = type(self).create_instance(kwargs.get("instance"), kwargs.get("address"), kwargs.get("port"))

        topic = getattr(self.instance, f"get{type(self).ty}Topic")(name)
        topic.setPersistent(persistent)
        self.sub = topic.subscribe(default)
        # Note for future testing: setRetained on topic may allow readonly props to not retain self.pub
        self.pub = topic.publish()
        self.pub.setDefault(default)

        def update(evt: ntcore.Event):
            value = getattr(evt.data.value, f"get{type(self).ty}")()
            self._update(value, remote=evt.is_(ntcore.EventFlags.kValueRemote))

        self.value_listener = self.instance.addListener(self.sub, ntcore.EventFlags.kValueRemote, update)

    def __del__(self):
        if self.instance is None:
            # Shouldn't ever happen, but just to be safe
            return
        self.instance.removeListener(self.value_listener)
        self.sub.close()
        if self.pub is not None:
            self.pub.close()
    
    def _update(self, value: Any, remote: bool=False):
        self._cached = value
        for binding in self.bindings:
            binding(value, remote)

    def bind(self, callback: Callable[[Any, bool], None]):
        self.bindings.append(callback)

    def get(self) -> Any:
        """Returns the current value of the property. The base implementation is sufficient for basic behaviour, however, the
        type signature returns an `Any`. Override the method and return `self._cached` if this is undesirable"""
        return self._cached

    def set(self, value: Any):
        if self.readonly:
            raise ValueError("Can't update a readonly property")
        self._update(value)
        self.pub.set(value)


class NTPropertyHost:
    def __setattr__(self, name, value):
        if not hasattr(self, name) and isinstance(value, NTProperty):
            if not hasattr(self, "_ntdict"):
                self._ntdict = {}
            self._ntdict[value.path] = value
            return super().__setattr__(name, value)
        elif isinstance(self.__dict__.get(name), NTProperty):
            self.__dict__[name].set(value)
            return value
        else:
            return super().__setattr__(name, value)

    def __getattribute__(self, name):
        if isinstance(super().__getattribute__(name), NTProperty):
            return super().__getattribute__(name).get()
        return super().__getattribute__(name)

    def bind(self, **kwargs: Callable[[Any, bool], None]):
        if not hasattr(self, "_ntdict"):
            return
        for name, callback in kwargs.items():
            if name in self._ntdict:
                self._ntdict[name].bind(callback)



class NumberProperty(NTProperty, ty="Double"):
    def __init__(self, name: str, default: float | int = 0.0, readonly: bool = False, persistent: bool = False, **kwargs):
        super().__init__(name, default, readonly, persistent, **kwargs)

    def get(self) -> float:
        return self._cached

    def set(self, value: float | int):
        if type(value) is not float and type(value) is not int:
            raise ValueError("Can not assign non-numeric to NumberProperty")
        super().set(value)


class BooleanProperty(NTProperty, ty="Boolean"):
    def __init__(self, name: str, default: bool = False, strict: bool = False, readonly: bool = False, persistent: bool = False, **kwargs):
        super().__init__(name, default, readonly, persistent, **kwargs)
        self.strict = strict

    def get(self) -> bool:
        return self._cached

    def set(self, value: bool):
        if self.strict and type(value) is not bool:
            raise ValueError("Can not assign non-boolean to BooleanProperty in strict mode")

        value = bool(value)
        super().set(value)


class StringProperty(NTProperty, ty="String"):
    def __init__(self, name: str, default: str = "", strict: bool = False, readonly = False, persistent: bool = False, **kwargs):
        super().__init__(name, default, readonly, persistent, **kwargs)
        self.strict = strict

    def get(self) -> str:
        return self._cached

    def set(self, value: str):
        if self.strict and type(value) is not str:
            raise ValueError("Can not assign non-string to StringProperty in strict mode")

        value = str(value)
        super().set(value)
