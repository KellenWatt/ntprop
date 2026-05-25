from typing import Any, ClassVar, Optional, Callable
import ntcore

class NTProperty:
    nt_instance: ClassVar[Optional[ntcore.NetworkTableInstance]] = None

    def __init_subclass__(cls, ty: str, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.ty = ty

    def __init__(self, name: str, default: Any = None, readonly: bool = False, force_publish: bool = True):
        if NTProperty.nt_instance is None:
            NTProperty.nt_instance = ntcore.NetworkTableInstance.getDefault()
        NTProperty.nt_instance.setServer("localhost", 0)
        NTProperty.nt_instance.startClient4("Reflection")

        self.bindings = []
        self.path = name
        self.default = default
        self._update(self.default, remote=False)
        #  self.cached = self.default
        topic = getattr(NTProperty.nt_instance, f"get{type(self).ty}Topic")(name)
        self.sub = topic.subscribe(default)
        if not readonly or force_publish:
            self.pub = topic.publish()
            if force_publish and readonly:
                self.pub.close()
                self.pub = None
        else:
            self.pub = None

        def update(evt: ntcore.Event):
            value = getattr(evt.data.value, f"get{type(self).ty}")()
            self._update(value, remote=True)

        self.value_listener = NTProperty.nt_instance.addListener(self.sub, ntcore.EventFlags.kValueAll, update)

    def __del__(self):
        if NTProperty.nt_instance is None:
            # Shouldn't every happen, but just to be safe
            return
        NTProperty.nt_instance.removeListener(self.value_listener)
        self.sub.close()
        if self.pub is not None:
            self.pub.close()
    
    def _update(self, value: Any, remote: bool=False):
        self._cached = value
        for binding in self.bindings:
            binding(value, remote)
    #  @property
    #  def cached(self) -> Any:
    #      return self._cached
    #  
    #  @cached.setter
    #  def cached(self, value: Any):
    #      for binding in self.bindings:
    #          binding(value)
    #      self._cached = value

    def bind(self, callback: Callable[[Any, bool], None]):
        self.bindings.append(callback)

    def get(self) -> Any:
        """Returns the current value of the property. The base implementation is sufficient for basic behaviour, however, the
        type signature returns an `Any`. Override the method and return `self._cached` if this is undesirable"""
        return self._cached

    def set(self, value: Any):
        raise NotImplementedError()


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
    def __init__(self, name: str, default: float | int = 0.0, readonly = False, force_publish: bool = True):
        super().__init__(name, default, readonly, force_publish)

    def get(self) -> float:
        return self._cached

    def set(self, value: float | int):
        if type(value) is not float and type(value) is not int:
            raise ValueError("Can not assign non-numeric to NumberProperty")
        self._update(value)
        self.pub.set(value)


class BooleanProperty(NTProperty, ty="Boolean"):
    def __init__(self, name: str, default: bool = False, readonly = False, strict: bool = False, force_publish: bool = True):
        super().__init__(name, default, readonly, force_publish)
        self.strict = strict

    def get(self) -> bool:
        return self._cached

    def set(self, value: bool):
        if self.strict and type(value) is not bool:
            raise ValueError("Can not assign non-boolean to BooleanProperty in strict mode")

        value = bool(value)
        self._update(value)
        self.pub.set(value)


class StringProperty(NTProperty, ty="String"):
    def __init__(self, name: str, default: str = "", readonly = False, strict: bool = False, force_publish: bool = True):
        super().__init__(name, default, readonly, force_publish)
        self.strict = strict

    def get(self) -> str:
        return self._cached

    def set(self, value: str):
        if self.strict and type(value) is not str:
            raise ValueError("Can not assign non-string to StringProperty in strict mode")

        value = str(value)
        self._update(value)
        self.pub.set(value)
