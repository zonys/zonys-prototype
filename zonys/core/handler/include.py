import pathlib

import mergedeep
import ruamel
import ruamel.yaml

import zonys
import zonys.core
import zonys.core.configuration
import zonys.core.util


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def before_configuration(
        event: "zonys.core.configuration.BeforeConfigurationEvent",
    ):
        path = pathlib.Path(event.options)
        if not path.is_absolute():
            path = event.base.joinpath(path)

        configuration = ruamel.yaml.YAML().load(zonys.core.util.open(path))

        if configuration is not None:
            event.manager.read(event.schemas, configuration, path.parent)

            event.configuration.update(
                mergedeep.merge(
                    configuration,
                    event.configuration,
                    strategy=mergedeep.Strategy.ADDITIVE,
                )
            )

        del event.configuration["include"]


SCHEMA = {
    "include": {
        "type": "string",
        "handler": _Handler,
    },
}
