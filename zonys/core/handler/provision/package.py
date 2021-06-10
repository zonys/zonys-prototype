import pathlib

import zonys
import zonys.core
import zonys.core.configuration
import zonys.core.freebsd.pkg


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_commit_after_create_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        zonys.core.freebsd.pkg.install(
            event.options,
            configuration=event.context["zone"].path.joinpath(
                pathlib.Path(zonys.core.freebsd.pkg.DEFAULT_CONFIGURATION_PATH.parts[1])
            ),
            root=event.context["zone"].path,
        )


SCHEMA = {
    "type": "dict",
    "allow_unknown": False,
    "schema": {
        "package": {
            "type": "list",
            "allow_unknown": False,
            "schema": {
                "type": "string",
            },
            "handler": _Handler,
        },
    },
}
