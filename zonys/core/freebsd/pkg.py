import pathlib
import subprocess
import typing

DEFAULT_CONFIGURATION_PATH = pathlib.Path("/", "etc", "pkg", "FreeBSD.conf")


def install(
    packages: typing.List[str],
    root: typing.Optional[typing.Union[pathlib.Path, str]] = None,
    configuration: typing.Optional[typing.Union[pathlib.Path, str]] = None,
    chroot: typing.Optional[typing.Union[pathlib.Path, str]] = None,
):
    if len(packages) == 0:
        return

    command = ["pkg"]

    flags = {
        "--config": configuration,
        "--root": root,
        "--chroot": chroot,
    }

    for (key, value) in flags.items():
        if value is not None:
            command.extend([key, str(value)])

    command.extend(["install", "-y", *packages])

    subprocess.run(
        command,
        check=True,
        # stdout=subprocess.DEVNULL,
        # stderr=subprocess.DEVNULL,
        # stdin=subprocess.DEVNULL,
    )
