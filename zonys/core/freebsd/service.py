import pathlib
import subprocess
import typing

import toolz


def installed(
    root: typing.Optional[pathlib.Path] = None,
) -> typing.Iterator[pathlib.Path]:
    if root is None:
        root = pathlib.Path("/")

    paths = [
        root.joinpath("etc", "rc.d"),
        root.joinpath("usr", "local", "etc", "rc.d"),
    ]

    return toolz.concat(
        list(
            map(
                lambda x: map(
                    lambda x: x,
                    x.iterdir(),
                ),
                filter(
                    lambda x: x.exists() and x.is_dir(),
                    paths,
                ),
            )
        )
    )


def enabled(jail_id: typing.Optional[int] = None) -> typing.Iterator[pathlib.Path]:
    flags = []

    if jail_id is not None:
        flags.extend(["-j", str(jail_id)])

    return map(
        pathlib.Path,
        subprocess.run(
            [
                "service",
                "-e",
                *flags,
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        ).stdout.split("\n")[:-1],
    )
