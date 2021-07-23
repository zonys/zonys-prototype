import pathlib
import tempfile
import unittest
import uuid

import zonys
import zonys.core
import zonys.core.namespace
import zonys.core.zone
import zonys.core.zfs
import zonys.core.zfs.file_system


class _TestZone(unittest.TestCase):
    def _test_file_system_structure(self, root: pathlib.Path):
        self.assertTrue(
            all(
                [
                    root.joinpath("directory").is_dir(),
                    root.joinpath("file").read_text() == "hello-world",
                    root.joinpath("file2").read_text() == "helloworld",
                    root.joinpath("link").is_symlink(),
                    root.joinpath("link").samefile(root.joinpath("file")),
                ]
            )
        )

    @classmethod
    def setUpClass(cls):
        cls._file_system = zonys.core.zfs.file_system.Identifier(
            [
                "zroot",
                "zonys",
                "test",
                str(uuid.uuid4()),
            ]
        ).use()

        cls._namespace = zonys.core.namespace.Handle(cls._file_system)

        cls._base = cls._namespace.zone_manager.zones.deploy(
            name="base",
            provision=[
                {
                    "directory": {
                        "path": "/directory",
                    },
                },
                {
                    "file": {
                        "path": "/file",
                        "content": "hello-world",
                    },
                },
                {
                    "file": {
                        "path": "/file2",
                        "prepend": "hello",
                        "append": "world",
                    },
                },
                {
                    "link": {
                        "source": "/file",
                        "destination": "/link",
                    },
                },
            ],
        )

        cls._snapshot_child = cls._namespace.zone_manager.zones.create(
            base=str(cls._base.uuid),
            name="snapshot-child",
        )

        with tempfile.TemporaryFile() as handle:
            cls._snapshot_child.send(handle.fileno())
            handle.seek(0)
            cls._redeploy_child = cls._namespace.zone_manager.zones.deploy(
                base=str(cls._base.uuid),
            ).redeploy(
                base=handle.fileno(),
                name="redeploy-child",
            )

    @classmethod
    def tearDownClass(cls):
        cls._redeploy_child.undeploy()
        cls._snapshot_child.undeploy()
        cls._base.undeploy()
        cls._file_system.destroy()

    def test_base_is_running(self):
        self.assertTrue(self._base.is_running())

    def test_base_name(self):
        self.assertEqual(self._base.name, "base")

    def test_base_file_system_structure(self):
        self._test_file_system_structure(self._base.path)

    def test_snapshot_child_base(self):
        self.assertEqual(str(self._snapshot_child.base.zone.uuid), str(self._base.uuid))

    def test_snapshot_child_name(self):
        self.assertEqual(self._snapshot_child.name, "snapshot-child")

    def test_snapshot_child_is_not_running(self):
        self.assertFalse(self._snapshot_child.is_running())

    def test_snapshot_child_file_system_structure(self):
        self._test_file_system_structure(self._snapshot_child.path)

    def test_redeploy_child_base(self):
        self.assertIsNone(self._redeploy_child.base)

    def test_redeploy_child_name(self):
        self.assertEqual(self._redeploy_child.name, "redeploy-child")

    def test_redeploy_child_is_running(self):
        self.assertTrue(self._redeploy_child.is_running())

    def test_redeploy_child_file_system_structure(self):
        self._test_file_system_structure(self._redeploy_child.path)


if __name__ == "main":  # pragma: no cover
    unittest.main()
