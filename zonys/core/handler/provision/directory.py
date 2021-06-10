import pathlib

import zonys
import zonys.core
import zonys.core.configuration


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_commit_after_create_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        path = pathlib.Path(event.options["path"])

        if not path.is_absolute():
            raise zonys.core.configuration.InvalidConfigurationError(
                "path must be absolute",
            )

        path = event.context["zone"].path.joinpath(
            *path.parts[1:],
        )

        path.mkdir(
            parents=True,
            exist_ok=True,
        )


SCHEMA = {
    "type": "dict",
    "allow_unknown": False,
    "schema": {
        "directory": {
            "type": "dict",
            "allow_unknown": False,
            "schema": {
                "path": {
                    "type": "string",
                    "required": True,
                },
            },
            "handler": _Handler,
        },
    },
}
