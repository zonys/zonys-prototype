import zonys
import zonys.core
import zonys.core.configuration
import zonys.core.freebsd
import zonys.core.freebsd.jail


class _Handler(zonys.core.configuration.Handler):
    @staticmethod
    def on_commit_after_create_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        if "afterCreate" in event.options:
            with zonys.core.freebsd.jail.temporary(
                str(event.context["zone"].uuid),
                event.context["zone"].path,
            ) as jail:
                for command in event.options["afterCreate"]:
                    jail.execute(command)

    @staticmethod
    def on_commit_after_start_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        if "beforeStart" in event.options:
            for command in event.options["beforeStart"]:
                event.context["jail"].execute(command)

        if event.options.get("rc", False):
            event.context["jail"].execute("/bin/sh /etc/rc")

        if "start" in event.options:
            for command in event.options["start"]:
                event.context["jail"].execute(command)

        if "afterStart" in event.options:
            for command in event.options["afterStart"]:
                event.context["jail"].execute(command)

    @staticmethod
    def on_commit_before_stop_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        if "beforeStop" in event.options:
            for command in event.options["beforeStop"]:
                event.context["jail"].execute(command)

        if "stop" in event.options:
            for command in event.options["stop"]:
                event.context["jail"].execute(command)

        if event.options.get("rc", False):
            event.context["jail"].execute("/bin/sh /etc/rc.shutdown")

        if "afterStop" in event.options:
            for command in event.options["afterStop"]:
                event.context["jail"].execute(command)

    @staticmethod
    def on_commit_before_destroy_zone(
        event: "zonys.core.configuration.CommitEvent",
    ):
        if "beforeDestroy" in event.options:
            with zonys.core.freebsd.jail.temporary(
                str(event.context["zone"].uuid),
                event.context["zone"].path,
            ) as jail:
                for command in event.options["beforeDestroy"]:
                    jail.execute(command)


SCHEMA = {
    "execute": {
        "type": "dict",
        "allow_unknown": False,
        "schema": {
            "afterCreate": {
                "type": "list",
                "schema": {
                    "type": "string",
                },
            },
            "beforeStart": {
                "type": "list",
                "schema": {
                    "type": "string",
                },
            },
            "start": {
                "type": "list",
                "schema": {
                    "type": "string",
                },
            },
            "afterStart": {
                "type": "list",
                "schema": {
                    "type": "string",
                },
            },
            "beforeStop": {
                "type": "list",
                "schema": {
                    "type": "string",
                },
            },
            "stop": {
                "type": "list",
                "schema": {
                    "type": "string",
                },
            },
            "afterStop": {
                "type": "list",
                "schema": {
                    "type": "string",
                },
            },
            "beforeDestroy": {
                "type": "list",
                "schema": {
                    "type": "string",
                },
            },
            "rc": {
                "type": "boolean",
            },
        },
        "handler": _Handler,
    }
}
