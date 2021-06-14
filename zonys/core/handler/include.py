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
    def on_prepend_configuration(
        event: "zonys.core.configuration.PrependConfigurationEvent",
    ):
        configuration = ruamel.yaml.YAML().load(zonys.core.util.open(event.options))

        if configuration is not None:
            del event.configuration["include"]

            event.prepend.update(configuration)
            event.configuration.update(mergedeep.merge(
                configuration,
                event.configuration,
                strategy=mergedeep.Strategy.ADDITIVE,
            ))


SCHEMA = {
    "include": {
        "type": "string",
        "handler": _Handler,
    },
}
