import pathlib
import shutil

import zonys
import zonys.core
import zonys.core.configuration

RESOLV_CONF_PATH = ["etc", "resolv.conf"]


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_normalize(event: "zonys.core.configuration.NormalizeEvent"):
        event.normalized.update(
            {"destination": event.context["zone"].path.joinpath(*RESOLV_CONF_PATH)}
        )

    @staticmethod
    def on_commit_before_start_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        source = pathlib.Path("/", *RESOLV_CONF_PATH)

        if event.normalized["destination"].exists():
            event.normalized["destination"].unlink()

        shutil.copy2(source, event.normalized["destination"])

        event.context["jail_configuration"]["ip4"] = "inherit"

    @staticmethod
    def on_commit_after_stop_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        if event.normalized["destination"].exists():
            event.normalized["destination"].unlink()


SCHEMA = {
    "network": {
        "oneof": [
            {
                "schema": {
                    "regex": "host",
                    "type": "string",
                },
                "handler": _Handler,
            }
        ],
    },
}
