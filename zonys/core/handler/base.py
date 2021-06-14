import mergedeep
import pathlib
import ruamel
import ruamel.yaml

import zonys
import zonys.core
import zonys.core.configuration


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_commit_before_create_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        if event.context.get("file_system", None) is not None:
            raise zonys.core.configuration.InvalidConfigurationError(
                "File system already provided"
            )

        file_system = None

        if isinstance(event.options, int):
            snapshot = None

            snapshot = event.context["file_system_identifier"].receive(event.options)

            file_system = snapshot.file_system

            path = snapshot.path.joinpath(".zonys.yaml")
            if path.exists():
                configuration = dict(ruamel.yaml.YAML().load(path))

                event.context["persistence"].update(
                    mergedeep.merge(
                        configuration,
                        event.context["persistence"],
                        strategy=mergedeep.Strategy.ADDITIVE,
                    )
                )
                event.configuration.update(
                    mergedeep.merge(
                        configuration.get("local", {}),
                        event.configuration,
                        strategy=mergedeep.Strategy.ADDITIVE,
                    )
                )

            snapshot.destroy()
        elif isinstance(event.options, str):
            parent = None

            path = pathlib.Path(event.options)
            if path.exists():
                configuration = ruamel.yaml.YAML().load(path)

                if "name" not in configuration:
                    raise zonys.core.configuration.InvalidConfigurationError(
                        "configuratoin does specify a name",
                    )

                identifier = configuration["name"]

                if identifier not in event.context["manager"].zones:
                    parent = event.context["manager"].zones.create(**configuration)
                else:
                    parent = event.context["manager"].zones.match_one(identifier)
            else:
                parent = event.context["manager"].zones.match_one(event.options)

            file_system = parent.snapshots["initial"].zfs_snapshot_handle.clone(
                event.context["file_system_identifier"],
            )

            event.context["persistence"].update(
                {
                    "base": str(parent.uuid),
                }
            )

        if file_system is None:
            raise zonys.core.configuration.InvalidConfigurationError(
                "Invalid base configuration"
            )

        event.context.update(
            {
                "file_system": file_system,
            }
        )

    @staticmethod
    def on_commit_before_create_snapshot(
        event: "zonys.core.configuration.CommitEvent",
    ):
        if event.configuration.get("base", None) is not None:
            del event.configuration["base"]


SCHEMA = {
    "base": {
        "handler": _Handler,
    }
}
