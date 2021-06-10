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

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.touch()

        if event.options.get("content") is not None:
            with path.open("w") as handle:
                handle.write(event.options["content"])

        if event.options.get("prepend") is not None:
            prepend = None

            with path.open("r") as handle:
                prepend = handle.read()

            with path.open("w") as handle:
                handle.write(event.options["prepend"])
                handle.write(prepend)

        if event.options.get("append") is not None:
            with path.open("a") as handle:
                handle.write(event.options["append"])


SCHEMA = {
    "type": "dict",
    "allow_unknown": False,
    "schema": {
        "file": {
            "schema": {
                "path": {
                    "type": "string",
                    "required": True,
                },
                "content": {
                    "type": "string",
                },
                "prepend": {
                    "type": "string",
                },
                "append": {
                    "type": "string",
                },
            },
            "handler": _Handler,
        },
    },
}
