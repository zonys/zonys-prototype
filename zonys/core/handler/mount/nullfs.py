import pathlib

import zonys
import zonys.core
import zonys.core.configuration
import zonys.core.freebsd
import zonys.core.freebsd.mount
import zonys.core.freebsd.mount.nullfs


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_normalize(
        event: "zonys.core.configuration.NormalizeEvent",
    ):
        destination = pathlib.Path(event.options["destination"])

        if not destination.is_absolute():
            raise zonys.core.configuration.Error(
                "destination path must be absolute",
            )

        destination = event.context["zone"].file_system.path.joinpath(
            *destination.parts[1:]
        )

        event.normalized.update(
            {
                "mountpoint": zonys.core.freebsd.mount.nullfs.Mountpoint(
                    event.options["source"],
                    destination,
                    event.options.get("read_only", True),
                ),
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


def _dict_schema(key: str):
    return {
        "type": "dict",
        "allow_unknown": False,
        "schema": {
            key: {
                "type": "dict",
                "allow_unknown": False,
                "schema": {
                    "destination": {
                        "type": "string",
                        "required": True,
                    },
                    "source": {
                        "type": "string",
                        "required": True,
                    },
                    "read_only": {
                        "type": "boolean",
                    },
                },
                "handler": _Handler,
            },
        },
    }


SCHEMA = {
    "oneof": [
        _dict_schema("nullfs"),
        _dict_schema("path"),
    ],
}
