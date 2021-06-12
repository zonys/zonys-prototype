import typing


class Error(RuntimeError):
    pass


class MultiKeyDictError(Error):
    pass


class KeyAlreadyUsedError(MultiKeyDictError):
    pass


class KeyNotExistsError(Error):
    pass


K = typing.TypeVar("K")
V = typing.TypeVar("V")


class MultiKeyDict(typing.Generic[K, V]):
    def __init__(self):
        self.__key_cliques: typing.Dict[K, typing.Tuple[K]] = {}
        self.__data: typing.Dict[typing.Tuple[K], V] = {}

    def __contains__(self, key: K) -> bool:
        return key in self.__key_cliques

    def __getitem__(self, key: K) -> V:
        if key not in self.__key_cliques:
            raise KeyNotExistsError()

        return self.__data[self.__key_cliques[key]]

    def __delitem__(self, key: K):
        if key not in self:
            raise KeyNotExistsError()

        key_clique = self.__key_cliques[key]

        for key_member in key_clique:
            del self.__key_cliques[key_member]

        del self.__data[key_clique]

    def __setitem__(
        self,
        keys: typing.Tuple[K],
        value: V,
    ):
        update = {}

        for key in keys:
            if key in self:
                raise KeyAlreadyUsedError()

            update.update(
                {
                    key: keys,
                }
            )

        self.__key_cliques.update(update)
        self.__data[keys] = value

    def keys(self) -> typing.List[K]:
        return list(self.__key_cliques.keys())

    def values(self) -> typing.List[V]:
        return list(self.__data.values())

    def clear(self):
        self.__key_cliques.clear()
        self.__data.clear()
