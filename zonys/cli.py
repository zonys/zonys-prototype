import pathlib
import sys
import typing

import click
import mergedeep
import rich
import rich.console
import rich.table
import ruamel
import ruamel.yaml

import zonys
import zonys.core
import zonys.core.namespace
import zonys.core.zfs
import zonys.core.zfs.file_system
import zonys.util

_pass_namespace = click.make_pass_decorator(zonys.core.namespace.Handle)


@click.option(
    "--namespace",
    "-n",
    "namespace",
    envvar="ZONYS_NAMESPACE",
    default="zroot/zonys",
    help="Root ZFS dataset of namespace.",
    show_default=True,
)
@click.group()
@click.pass_context
def main(ctx: click.Context, namespace: str):
    file_system_identifier = zonys.core.zfs.file_system.Identifier(
        namespace,
    )

    file_system = None

    if file_system_identifier.exists():
        file_system = file_system_identifier.open()
    else:
        file_system = file_system_identifier.create()

        if not file_system.is_mounted():
            file_system.mount()

    ctx.obj = zonys.core.namespace.Handle(file_system)


@main.group(
    name="service",
)
def _service():
    pass


@_service.command(name="enable", help="Register the namespace as service.")
@_pass_namespace
def _service_enable(namespace):
    namespace.service.enable()


@_service.command(name="disable", help="Unregister the namespace as service.")
@_pass_namespace
def _service_disable(namespace):
    namespace.service.disable()


@_service.command(name="start", help="Start the service.")
@_pass_namespace
def _service_start(namespace):
    namespace.service.start()


@_service.command(name="stop", help="Stop the service.")
@_pass_namespace
def _service_stop(namespace):
    namespace.service.stop()


@_service.command(name="restart", help="Restart the service.")
@_pass_namespace
def _service_restart(namespace):
    namespace.service.restart()


@_service.command(name="status", help="Show the status.")
@_pass_namespace
def _service_status(namespace):
    namespace.service.status()


@main.group(
    name="zone",
)
def _zone():
    pass


@_zone.command(
    name="status",
    help="Show the zone status.",
)
@_pass_namespace
def _zone_status(
    namespace: "zonys.core.namespace.Handle",
):
    table = rich.table.Table()

    table.add_column("UUID")
    table.add_column("Name")
    table.add_column("Base")
    table.add_column("Snapshots")
    table.add_column("Status")

    for zone in namespace.zone_manager.zones:
        status = "Down"
        if zone.is_running():
            status = "Up"

        base = zone.base
        base_output = ""
        if base is not None:
            base_output = "{}@{}".format(
                base.zone_handle.identifier,
                base.name,
            )

        table.add_row(
            str(zone.uuid),
            zone.name,
            base_output,
            ", ".join(map(lambda x: x.name, zone.snapshots)),
            status,
        )

    rich.console.Console().print(table)


def _zone_handle_configuration(
    arguments: typing.Tuple[typing.Any],
) -> typing.Dict[str, typing.Any]:
    configuration: typing.Dict[str, typing.Any] = {}

    i = 0
    while i < len(arguments):
        if arguments[i] == "-":
            configuration["base"] = sys.stdin.fileno()
        else:
            first, second = arguments[i], arguments[i + 1]

            if first.startswith("--"):
                first = first[2:]

            configuration.update(
                {
                    first: second,
                }
            )

            i = i + 1

        i = i + 1

    return configuration


@_zone.command(
    name="create",
    help="Create a new zone.",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument(
    "arguments",
    nargs=-1,
    type=click.UNPROCESSED,
)
@_pass_namespace
def _zone_create(
    namespace: "zonys.core.namespace.Handle",
    arguments: typing.Tuple[typing.Any],
):
    configuration = _zone_handle_configuration(arguments)
    print(namespace.zone_manager.zones.create(**configuration).identifier)


@_zone.command(
    name="run",
    help="Create and start a new temporary zone.",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument(
    "arguments",
    nargs=-1,
    type=click.UNPROCESSED,
)
@_pass_namespace
def _zone_run(
    namespace: "zonys.core.namespace.Handle",
    arguments: typing.Tuple[typing.Any],
):
    configuration = _zone_handle_configuration(arguments)
    print(namespace.zone_manager.zones.run(**configuration).identifier)


@_zone.command(
    name="replace",
    help="Replace a zone.",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument(
    "identifier",
)
@click.argument(
    "arguments",
    nargs=-1,
    type=click.UNPROCESSED,
)
@_pass_namespace
def _zone_replace(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
    arguments: typing.Tuple[typing.Any],
):
    configuration = _zone_handle_configuration(arguments)
    namespace.zone_manager.zones.replace(identifier, **configuration)


@_zone.command(
    name="deploy",
    help="Create and start a new zone.",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument(
    "arguments",
    nargs=-1,
    type=click.UNPROCESSED,
)
@_pass_namespace
def _zone_deploy(
    namespace: "zonys.core.namespace.Handle",
    arguments: typing.Tuple[typing.Any],
):
    configuration = _zone_handle_configuration(arguments)
    print(namespace.zone_manager.zones.deploy(**configuration).identifier)


@_zone.command(
    name="undeploy",
    help="Stop and destroy a zone.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_undeploy(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    namespace.zone_manager.zones.match(identifier)[0].undeploy()


@_zone.command(
    name="redeploy",
    help="Undeploy a zone and deploy a new zone.",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@click.argument(
    "identifier",
)
@click.argument(
    "arguments",
    nargs=-1,
    type=click.UNPROCESSED,
)
@_pass_namespace
def _zone_redeploy(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
    arguments: typing.Tuple[typing.Any],
):
    configuration = _zone_handle_configuration(arguments)
    print(
        namespace.zone_manager.zones.match(identifier)[0]
        .redeploy(**configuration)
        .identifier
    )


@_zone.command(
    name="destroy",
    help="Destroy a zone.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_destroy(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    namespace.zone_manager.zones.match(identifier)[0].destroy()


@_zone.command(
    name="start",
    help="Start a zone.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_start(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    namespace.zone_manager.zones.match(identifier)[0].start()


@_zone.command(
    name="stop",
    help="Stop a zone.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_stop(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    namespace.zone_manager.zones.match(identifier)[0].stop()


@_zone.command(
    name="restart",
    help="Stop and start a zone.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_restart(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    namespace.zone_manager.zones.match(identifier)[0].restart()


@_zone.command(
    name="up",
    help="Start a zone if it is not running.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_up(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    namespace.zone_manager.zones.match(identifier)[0].up()


@_zone.command(
    name="down",
    help="Stop a zone if it is not running.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_down(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    namespace.zone_manager.zones.match(identifier)[0].down()


@_zone.command(
    name="reup",
    help="Stop a zone if it not running and start it afterwards.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_reup(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    namespace.zone_manager.zones.match(identifier)[0].reup()


@_zone.command(
    name="send",
    help="Send a zone to a destination.",
)
@click.option(
    "-d",
    "--destination",
    "destination",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_send(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
    destination: typing.Optional[str],
):
    target = None

    if destination is None:
        target = sys.stdout.fileno()
    else:
        target = destination

    namespace.zone_manager.zones.match(identifier)[0].send(target)


@_zone.command(
    name="path",
    help="Print the path of a zone.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_path(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    print(namespace.zone_manager.zones.match(identifier)[0].path)


@_zone.command(
    name="console",
    help="Starts the console of a zone.",
)
@click.argument(
    "identifier",
)
@_pass_namespace
def _zone_console(
    namespace: "zonys.core.namespace.Handle",
    identifier: str,
):
    namespace.zone_manager.zones.match(identifier)[0].console(
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    main()
