import pathlib
import typing

import zonys
import zonys.core
import zonys.core.configuration
import zonys.core.freebsd
import zonys.core.freebsd.mount
import zonys.core.freebsd.mount.devfs


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_normalize(
        event: "zonys.core.configuration.NormalizeEvent",
    ):
        path = pathlib.Path("/dev")
        ruleset = None
        include = None

        if isinstance(event.options, dict):
            if "path" in event.options:
                path = pathlib.Path(event.options["path"])

            if "ruleset" in event.options:
                ruleset = event.options["ruleset"]

            if "include" in event.options:
                include = event.options["include"]

        if not path.is_absolute():
            raise zonys.core.configuration.Error(
                "destination {} must be an absolute path".format(
                    str(path),
                ),
            )

        path = event.context["zone"].path.joinpath(*path.parts[1:])

        event.normalized.update(
            {
                "mountpoint": zonys.core.freebsd.mount.devfs.Mountpoint(path),
                "ruleset": ruleset,
                "include": include,
            }
        )

    @staticmethod
    def on_commit_before_start_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        handle = None

        try:
            if not event.normalized["mountpoint"].exists():
                handle = event.normalized["mountpoint"].mount()
            else:
                handle = event.normalized["mountpoint"].open()

            for include in event.normalized.get("include", []):
                handle.rules.unhide_path(include)

        except:
            if handle is not None:
                handle.unmount()

            raise

    @staticmethod
    def on_rollback_before_start_zone(
        event: "zonys.core.configuration.RollbackEvent",
    ):
        if event.normalized["mountpoint"].exists():
            event.normalized["mountpoint"].open().unmount()

    @staticmethod
    def on_commit_after_stop_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        if event.normalized["mountpoint"].exists():
            event.normalized["mountpoint"].open().unmount()


def _dict_schema(key: str) -> typing.Dict[typing.Any, typing.Any]:
    return {
        "type": "dict",
        "allow_unknown": False,
        "schema": {
            key: {
                "type": "dict",
                "allow_unknown": False,
                "schema": {
                    "path": {
                        "type": "string",
                    },
                    "include": {
                        "type": "list",
                        "schema": {
                            "type": "string",
                        },
                    },
                },
                "handler": _Handler,
            },
        },
    }


SCHEMA = {
    "oneof": [
        _dict_schema("devices"),
        _dict_schema("device"),
        _dict_schema("devfs"),
        _dict_schema("dev"),
        {
            "type": "string",
            "regex": "devices|device|devfs|dev",
            "handler": _Handler,
        },
    ],
}
