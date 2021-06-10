import typing
import subprocess


def update(key: str, value: str):
    subprocess.run(
        [
            "sysrc",
            "{}={}".format(key, value),
        ],
        check=True,
        # stdout=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def items() -> typing.Dict[str, str]:
    return dict(
        map(
            lambda x: (x[0].strip(), ":".join(x[1:]).strip()),
            map(
                lambda x: x.split(":"),
                subprocess.run(
                    [
                        "sysrc",
                        "-A",
                    ],
                    check=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ).stdout.split("\n")[:-1],
            ),
        )
    )


def delete(key: str):
    subprocess.run(
        [
            "sysrc",
            "-x",
            key,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def get(key: str, default: typing.Any = None) -> typing.Any:
    return items().get(key, default)
