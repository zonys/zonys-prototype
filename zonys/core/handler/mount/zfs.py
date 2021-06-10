import zonys
import zonys.core
import zonys.core.configuration
import zonys.core.zfs
import zonys.core.zfs.file_system


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_prepend_configuration(
        event: "zonys.core.configuration.PrependConfigurationEvent",
    ):
        event.prepend.update(
            {
                "mount": [
                    {
                        "devfs": {
                            "include": [
                                "zfs",
                                "null",
                                "zero",
                            ],
                        },
                    },
                ],
            }
        )

    @staticmethod
    def on_normalize(
        event: "zonys.core.configuration.NormalizeEvent",
    ):
        event.normalized.update(
            {
                "file_system": zonys.core.zfs.file_system.Identifier(
                    event.options,
                ).open(),
            }
        )

    @staticmethod
    def on_commit_before_start_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        event.normalized["file_system"].properties["jailed"].enable()

        event.context["jail_configuration"]["allow.mount"] = True
        event.context["jail_configuration"]["allow.mount.zfs"] = True
        event.context["jail_configuration"]["enforce_statfs"] = 0
        event.context["jail_configuration"]["children.max"] = 100

    @staticmethod
    def on_rollback_before_start_zone(
        event: "zonys.core.configuration.RollbackEvent",
    ):
        event.normalized["file_system"].properties["jailed"].inherit()

    @staticmethod
    def on_commit_after_start_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        event.normalized["file_system"].jail(event.context["jail"])

        event.context["jail"].execute(
            "zfs mount {}".format(str(event.normalized["file_system"].identifier))
        )

    @staticmethod
    def on_rollback_after_start_zone(
        event: "zonys.core.configuration.RollbackEvent",
    ):
        event.context["jail"].execute(
            "zfs unmount {}".format(str(event.normalized["file_system"].identifier))
        )

        event.normalized["file_system"].unjail(event.context["jail"])

    @staticmethod
    def on_commit_before_stop_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        event.context["jail"].execute(
            "zfs unmount {}".format(str(event.normalized["file_system"].identifier))
        )

        event.normalized["file_system"].unjail(event.context["jail"])

    @staticmethod
    def on_commit_after_stop_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        event.normalized["file_system"].properties["jailed"].inherit()


SCHEMA = {
    "type": "dict",
    "allow_unknown": False,
    "schema": {
        "zfs": {
            "type": "string",
            "required": True,
            "handler": _Handler,
        },
    },
}
