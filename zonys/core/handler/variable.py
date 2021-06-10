import zonys
import zonys.core
import zonys.core.configuration


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_attach(
        event: "zonys.core.configuration.AttachEvent",
    ):
        event.manager.variables.update(event.options)


SCHEMA = {
    "variable": {
        "type": "dict",
        "handler": _Handler,
    },
}
