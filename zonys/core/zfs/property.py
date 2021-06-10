import zonys
import zonys.core
import zonys.core.zfs

ENABLED_VALUE = "on"
DISABLED_VALUE = "off"


class Error(RuntimeError):
    pass


class InvalidValueError(Error):
    def __init__(self, value, handle):
        super().__init__(
            "Value {} is not valid for property {}".format(
                value,
                handle.name,
            )
        )


class Handle(zonys.core.zfs.Handle):
    def __init__(self, descriptor):
        super().__init__(descriptor)

    @property
    def name(self):
        return self._descriptor.name

    @property
    def value(self):
        return self._descriptor.value

    @property
    def allowed_values(self):
        return self._descriptor.allowed_values

    @value.setter
    def value(self, value):
        if value not in self.allowed_values:
            raise InvalidValueError(value, self)

        self._descriptor.value = value

    def is_enabled(self):
        return self._descriptor.value == ENABLED_VALUE

    def is_disabled(self):
        return self._descriptor.value == DISABLED_VALUE

    def enable(self):
        self.value = ENABLED_VALUE

    def disable(self):
        self.value = DISABLED_VALUE

    def is_on(self):
        return self.is_enabled()

    def is_off(self):
        return self.is_off()

    def on(self):
        return self.enable()

    def off(self):
        return self.disable()

    def inherit(self):
        self._descriptor.inherit()
