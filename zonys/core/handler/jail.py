import pathlib

import zonys
import zonys.core
import zonys.core.configuration
import zonys.core.util


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_commit_before_start_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        event.context["jail_configuration"].update(
            **event.options
        )


SCHEMA = {
    "jail": {
        "type": "dict",
        "handler": _Handler,
    },
}
