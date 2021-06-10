from subprocess import Popen
import io
import os
import random
import shutil
import stat
import tempfile
import typing
import urllib

import pathlib
import pycurl


class Context:
    def __init__(self, enter, exit):
        self._enter = enter
        self._exit = exit

    def __enter__(self):
        self._enter()

    def __exit__(self, *args):
        self._exit(*args)


class Box:
    def __init__(self, value=None):
        self.__value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value


class InvalidUri(RuntimeError):
    def __init__(self, uri):
        super().__init__("URI {} is invalid", uri)


def open(uri):
    if isinstance(uri, str):
        uri = urllib.parse.urlparse(uri)
    elif isinstance(uri, pathlib.Path):
        return uri.open("r")
    elif not isinstance(uri, urllib.parse.ParseResult):
        raise InvalidUri(uri)

    if len(uri.scheme) == 0 and len(uri.netloc) == 0:
        return pathlib.Path(uri.path).open("r")

    buffer = io.BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, uri.geturl())
    c.setopt(c.WRITEDATA, buffer)

    c.perform()

    c.close()

    return buffer


def mirror(source, destination, extract=False):
    source_url = None

    if isinstance(source, str):
        source_url = urllib.parse.urlparse(source)
    elif isinstance(source, pathlib.Path):
        source_url = urllib.parse.ParseResult(
            scheme="",
            netloc="",
            path=source,
            query="",
            params="",
            fragment="",
        )
    elif isinstance(source, urllib.parse.ParseResult):
        source_url = source
    else:
        raise TypeError("source must be instance of str, Path or ParseResult")

    source_path = pathlib.Path(source_url.path)

    if isinstance(destination, str):
        destination = pathlib.Path(destination)
    elif not isinstance(destination, pathlib.Path):
        raise TypeError("destination must be instance of str or Path")

    if len(source_url.netloc) == 0:
        if source_path.is_file():
            if extract:
                shutil.unpack_archive(source_path, destination)
            else:
                raise NotImplementedError()
        elif source.is_dir() and destination.is_dir():
            shutil.copytree(
                source,
                destination,
                symlinks=True,
                ignore_dangling_symlinks=True,
                dirs_exist_ok=True,
            )
        else:
            raise NotImplementedError()
    else:
        with tempfile.NamedTemporaryFile(suffix=source_path.suffix) as handle:
            curl = pycurl.Curl()
            curl.setopt(curl.URL, source_url.geturl())
            curl.setopt(curl.WRITEDATA, handle)
            curl.perform()
            curl.close()

            handle.seek(0)

            shutil.unpack_archive(handle.name, destination)


def remove(path):
    pass


def destroy_tree(path):
    def remove_readonly(func, path, _):
        os.chflags(path, 0)
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(str(path), onerror=remove_readonly)
