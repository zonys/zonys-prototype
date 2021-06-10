import zonys
import zonys.core
import zonys.core.configuration


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_commit_after_stop_zone(event: "zonys.core.configuration.CommitEvent"):
        if event.options:
            event.context["zone"].destroy()


SCHEMA = {
    "temporary": {
        "type": "boolean",
        "handler": _Handler,
    }
}
