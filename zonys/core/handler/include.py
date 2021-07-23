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
    def on_normalize(event: "zonys.core.configuration.NormalizeEvent"):
        event.normalized.update(
            {
                "name": pathlib.Path(event.options),
            }
        )

    @staticmethod
    def before_configuration(
        event: "zonys.core.configuration.BeforeConfigurationEvent",
    ):
        configuration = ruamel.yaml.YAML().load(zonys.core.util.open(event.options))

        if configuration is not None:
            event.manager.read(event.schemas, configuration)

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
