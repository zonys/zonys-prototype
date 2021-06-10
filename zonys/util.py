#!/usr/bin/env python3

import typing


class Netloc:
    def __init__(
        self,
        parse: typing.Optional[str] = None,
        hostname: str = "",
        username: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
    ):
        if parse is not None:
            split = parse.split("@")

            if len(split) == 1:
                hostname = split[0]
            elif len(split) == 2:
                hostname = split[1]
                split = split[0].split(":")
                if len(split) == 1:
                    username = split[0]
                elif len(split) == 2:
                    username = split[0]
                    password = split[1]
                else:
                    raise RuntimeError("Invalid authority")
            else:
                raise RuntimeError("Invalid netloc")

        self.username = username
        self.password = password
        self.hostname = hostname

    def __str__(self) -> str:
        string = ""

        if self.username is not None:
            string += self.username

            if self.password is not None:
                string += ":{}".format(self.password)

            string += "@"

        string += self.hostname

        return string
