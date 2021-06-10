import pathlib

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
            event.configuration.update(configuration)
            event.prepend.update(configuration)

        del event.configuration["include"]


SCHEMA = {
    "include": {
        "type": "string",
        "handler": _Handler,
    },
}
