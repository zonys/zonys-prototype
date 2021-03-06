import pathlib
import shutil

import zonys
import zonys.core
import zonys.core.util
import zonys.core.configuration


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_commit_after_create_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        destination = pathlib.Path(event.options["destination"])

        if not destination.is_absolute():
            raise zonys.core.configuration.InvalidConfigurationError(
                "destination path must be absolute",
            )

        destination = event.context["zone"].path.joinpath(
            *destination.parts[1:],
        )

        source = pathlib.Path(event.options["source"])
        if not source.is_absolute():
            source = event.base.joinpath(source)

        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copyfile(source, destination)


SCHEMA = {
    "type": "dict",
    "allow_unknown": False,
    "schema": {
        "path": {
            "type": "dict",
            "allow_unknown": False,
            "schema": {
                "source": {
                    "type": "string",
                    "required": True,
                },
                "destination": {
                    "type": "string",
                    "required": True,
                },
            },
            "handler": _Handler,
        },
    },
}
