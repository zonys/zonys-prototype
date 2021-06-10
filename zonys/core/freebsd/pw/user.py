import pathlib
import typing
import subprocess

DEFAULT_CONFIGURATION_PATH = pathlib.Path(
    "/",
    "etc",
    "pw.conf",
)

# pylint: disable=too-many-arguments
def add(
    name: str,
    root: typing.Optional[typing.Union[pathlib.Path, str]] = None,
    configuration: typing.Optional[typing.Union[pathlib.Path, str]] = None,
    shell: typing.Optional[str] = None,
    comment: typing.Optional[str] = None,
    home: typing.Optional[typing.Union[pathlib.Path, str]] = None,
):
    command = ["pw", "user", "add", name]

    flags = {
        "-R": root,
        "-C": configuration,
        "-c": comment,
        "-d": home,
        "-s": shell,
    }

    for (key, value) in flags.items():
        if value is not None:
            command.extend([key, str(value)])

    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
