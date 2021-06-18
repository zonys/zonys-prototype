import zonys
import zonys.core
import zonys.core.configuration


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_commit_before_create_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        event.context["persistence"].update(
            {
                "name": event.options,
            }
        )


SCHEMA = {
    "name": {
        "type": "string",
        "handler": _Handler,
    }
}
