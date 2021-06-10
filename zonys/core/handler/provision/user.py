"""
import zonys
import zonys.configuration
import zonys.freebsd
import zonys.freebsd.pw
import zonys.freebsd.pw.user


class _Handler(zonys.configuration.Handler):
    @staticmethod
    def on_commit_after_create_zone(
        event: "zonys.configuration.CommitEvent",
    ):
        configuration = event.context["zone"].path.joinpath(
            *zonys.freebsd.pw.user.DEFAULT_CONFIGURATION_PATH.parts[1:],
        )

        if not configuration.exists():
            configuration = None

        kwargs = {
            "name": event.options["name"],
            "shell": event.options.get("shell", None),
            "comment": event.options.get("comment", None),
            "home": event.options.get("home", None),
            "root": event.context["zone"].path,
            "configuration": configuration,
        }

        zonys.freebsd.pw.user.add(**kwargs)


SCHEMA = {
    "user": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {
                    "type": "string",
                    "required": True,
                },
                "home": {
                    "type": "string",
                },
                "shell": {
                    "type": "string",
                },
                "comment": {
                    "type": "string",
                },
            },
            "handler": _Handler,
        },
    },
}

"""

SCHEMA = {}
