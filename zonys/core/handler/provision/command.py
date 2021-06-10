import zonys
import zonys.core
import zonys.core.configuration
import zonys.core.freebsd
import zonys.core.freebsd.jail


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_commit_after_create_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        with zonys.core.freebsd.jail.temporary(
            str(event.context["zone"].uuid),
            event.context["zone"].path,
        ) as jail:
            jail.execute(event.options)


SCHEMA = {
    "oneof": [
        {
            "type": "string",
            "handler": _Handler,
        },
        {
            "type": "dict",
            "allow_unknown": False,
            "schema": {
                "command": {
                    "type": "string",
                    "handler": _Handler,
                },
            },
        },
    ],
}
