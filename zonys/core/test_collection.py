import unittest

import zonys
import zonys.core
import zonys.core.collection


class TestMultiKeyDict(unittest.TestCase):
    def setUp(self):
        self.instance: zonys.core.collection.MultiKeyDict[
            str, int
        ] = zonys.core.collection.MultiKeyDict()

    def test_get_invalid_key(self):
        with self.assertRaises(zonys.core.collection.KeyNotExistsError):
            self.instance["key"]

    def test_del_invalid_key(self):
        with self.assertRaises(zonys.core.collection.KeyNotExistsError):
            del self.instance["key"]

    def test_single_key_in(self):
        self.instance[("key",)] = 100
        assert "key" in self.instance

    def test_multi_key_in(self):
        self.instance[("key1", "key2")] = 100
        assert "key2" in self.instance

    def test_single_key_getitem(self):
        self.instance[("key",)] = 100
        assert self.instance["key"] == 100

    def test_multi_key_getitem0(self):
        self.instance[("key1", "key2")] = 100
        assert self.instance["key1"] == 100

    def test_multi_key_getitem1(self):
        self.instance[("key1", "key2")] = 100
        assert self.instance["key2"] == 100

    def test_multi_key_delitem0(self):
        self.instance[("key1", "key2")] = 100
        del self.instance["key1"]
        assert "key1" not in self.instance

    def test_multi_key_delitem1(self):
        self.instance[("key1", "key2")] = 100
        del self.instance["key1"]
        assert len(self.instance.values()) == 0

    def test_multi_key_delitem2(self):
        self.instance[("key1", "key2")] = 100
        del self.instance["key1"]
        assert len(self.instance.keys()) == 0

    def test_shared_key_insert(self):
        self.instance[("key1", "key2")] = 100

        with self.assertRaises(zonys.core.collection.KeyAlreadyUsedError):
            self.instance[("key2", "key3")] = 100

    def test_clear(self):
        self.instance.clear()
        assert "key1" not in self.instance


if __name__ == "main":  # pragma: no cover
    unittest.main()
