import pathlib

import git

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

        git.Repo.clone_from(
            event.options["url"],
            path,
            branch=event.options.get("object", None),
        )


SCHEMA = {
    "type": "dict",
    "allow_unknown": False,
    "schema": {
        "git": {
            "type": "dict",
            "allow_unknown": False,
            "schema": {
                "url": {
                    "type": "string",
                    "required": True,
                },
                "path": {
                    "type": "string",
                    "required": True,
                },
                "object": {
                    "type": "string",
                },
            },
            "handler": _Handler,
        }
    },
}
