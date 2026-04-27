from typing import Any, ClassVar, Optional
import ntcore

class NTProperty:
    nt_instance: ClassVar[Optional[ntcore.NetworkTableInstance]] = None

    def __init__(self):
        if NTProperty.nt_instance is None:
            NTProperty.nt_instance = ntcore.NetworkTableInstance.getDefault()
        NTProperty.nt_instance.setServer("localhost", 0)
        NTProperty.nt_instance.startClient4("Reflection")

    def get(self) -> Any:
        raise NotImplementedError()

    def set(self, value: Any):
        raise NotImplementedError()


class NTPropertyHost:
    def __setattr__(self, name, value):
        if isinstance(name, NTProperty):
            self.__dict__[name].set(value)
            return value
        else:
            return super().__setattr__(name, value)

    def __getattribute__(self, name):
        if hasattr(self, name) and isinstance(self.__dict__[name], NTProperty):
            return self.__dict__[name].get()
        return super().__getattribute__(name)


class NumberProperty(NTProperty):
    def __init__(self, name: str, default: float | int = 0.0, readonly = False):
        super().__init__()
        self.default = default
        self.cached = self.default
        topic = NTProperty.nt_instance.getDoubleTopic(name)
        self.sub = topic.subscribe(default)
        if not readonly:
            self.pub = topic.publish()
        else:
            self.pub = None

        def update(evt: ntcore.Event):
            value = value.getDouble()
            self.cached = value

        self.value_listener = NTProperty.nt_instance.addListener(self.sub, ntcore.EventFlags.kValueAll, update)

    def __del__(self):
        NTProperty.nt_instance.remove_listener(self.value_listener)
        self.sub.close()
        if self.pub is not None:
            self.pub.close()

    def get(self) -> float:
        return self.cached

    def set(self, value: float | int):
        if value is not float and value is not int:
            raise ValueError("Can not assign non-numeric to NumberProperty")
        self.cached = value
        self.pub.set(value)


class BooleanProperty(NTProperty):
    def __init__(self, name: str, default: bool = False, readonly = False, strict: bool = False):
        super().__init__()
        self.default = default
        self.cached = self.default
        self.strict = strict
        topic = NTProperty.nt_instance.getBooleanTopic(name)
        self.sub = topic.subscribe(default)
        if not readonly:
            self.pub = topic.publish()
        else:
            self.pub = None

        def update(evt: ntcore.Event):
            value = value.getBoolean()
            self.cached = value

        self.value_listener = NTProperty.nt_instance.addListener(self.sub, ntcore.EventFlags.kValueAll, update)

    def __del__(self):
        NTProperty.nt_instance.remove_listener(self.value_listener)
        self.sub.close()
        if self.pub is not None:
            self.pub.close()

    def get(self) -> bool:
        return self.cached

    def set(self, value: bool):
        if self.strict and value is not bool:
            raise ValueError("Can not assign non-boolean to BooleanProperty in strict mode")

        value = bool(value)
        self.cached = value
        self.pub.set(value)


class StringProperty(NTProperty):
    def __init__(self, name: str, default: bool, readonly = False, strict: bool = False):
        super().__init__()
        self.default = default
        self.cached = self.default
        self.strict = strict
        topic = NTProperty.nt_instance.getStringTopic(name)
        self.sub = topic.subscribe(default)
        if not readonly:
            self.pub = topic.publish()
        else:
            self.pub = None

        def update(evt: ntcore.Event):
            value = value.getString()
            self.cached = value

        self.value_listener = NTProperty.nt_instance.addListener(self.sub, ntcore.EventFlags.kValueAll, update)

    def __del__(self):
        NTProperty.nt_instance.remove_listener(self.value_listener)
        self.sub.close()
        if self.pub is not None:
            self.pub.close()

    def get(self) -> str:
        return self.cached

    def set(self, value: str):
        if self.strict and value is not str:
            raise ValueError("Can not assign non-string to StringProperty in strict mode")

        value = str(value)
        self.cached = value
        self.pub.set(value)
