import shutil
import tempfile
import unittest
import uuid

import zonys
import zonys.core
import zonys.core.namespace
import zonys.core.zone
import zonys.core.zfs
import zonys.core.zfs.file_system


class _Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._file_system = zonys.core.zfs.file_system.Identifier([
            "zroot",
            "zonys",
            "test",
            str(uuid.uuid4()),
        ]).use()

        cls._namespace = zonys.core.namespace.Handle(cls._file_system)

    @classmethod
    def tearDownClass(cls):
        cls._file_system.destroy()

class _TestZoneSimpleCreate(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.create()

    def tearDown(self):
        self._zone.destroy()

    def test_zfs_file_system(self):
        identifier = zonys.core.zfs.file_system.Identifier(*self._zone.path.parts[1:])
        self.assertTrue(identifier.exists())

class _TestZoneSimpleDestroy(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.create()
        self._zone.destroy()

    def test_zfs_file_system(self):
        identifier = zonys.core.zfs.file_system.Identifier(*self._zone.path.parts[1:])
        self.assertFalse(identifier.exists())

class _TestZoneSimpleStart(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.create()
        self._zone.start()

    def tearDown(self):
        self._zone.undeploy()

    def test_is_running(self):
        self.assertTrue(self._zone.is_running())


class _TestZoneSimpleStop(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.create()
        self._zone.start()
        self._zone.stop()

    def tearDown(self):
        self._zone.undeploy()

    def test_is_running(self):
        self.assertFalse(self._zone.is_running())


class _TestZoneSimpleRestart(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.create()
        self._zone.start()
        self._zone.restart()

    def tearDown(self):
        self._zone.undeploy()

    def test_is_running(self):
        self.assertTrue(self._zone.is_running())


class _TestZoneSimpleDeploy(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.deploy()

    def tearDown(self):
        self._zone.undeploy()

    def test_zfs_file_system(self):
        identifier = zonys.core.zfs.file_system.Identifier(*self._zone.path.parts[1:])
        self.assertTrue(identifier.exists())

    def test_is_running(self):
        self.assertTrue(self._zone.is_running())


class _TestZoneSimpleUndeploy(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.deploy()
        self._zone.undeploy()

    def test_zfs_file_system(self):
        identifier = zonys.core.zfs.file_system.Identifier(*self._zone.path.parts[1:])
        self.assertFalse(identifier.exists())

    def test_is_running(self):
        self.assertFalse(self._zone.is_running())


class _TestZoneSimpleRunStart(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.run()

    def tearDown(self):
        self._zone.undeploy()

    def test_zfs_file_system(self):
        identifier = zonys.core.zfs.file_system.Identifier(*self._zone.path.parts[1:])
        self.assertTrue(identifier.exists())

    def test_is_running(self):
        self.assertTrue(self._zone.is_running())


class _TestZoneSimpleRunStop(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.run()
        self._zone.stop()

    def test_zfs_file_system(self):
        identifier = zonys.core.zfs.file_system.Identifier(*self._zone.path.parts[1:])
        self.assertFalse(identifier.exists())

    def test_is_running(self):
        self.assertFalse(self._zone.is_running())

class _TestZoneName(_Test):
    def setUp(self):
        self._zone = self._namespace.zone_manager.zones.create(name="hello_world")

    def tearDown(self):
        self._zone.destroy()

    def test_zone_name(self):
        self.assertEqual(self._zone.name, "hello_world")

    def test_zones_match_one(self):
        self.assertEqual(
            self._zone.uuid,
            self._namespace.zone_manager.zones.match_one(self._zone.name).uuid,
        )

class _TestZoneProvision(_Test):
    def setUp(self):
        self._tempfile = tempfile.NamedTempFile()
        #self._zipfile = zipfile.ZipFile()

        self._zone = self._namespace.zone_manager.zones.create(provision=[
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
        ])

    def tearDown(self):
        self._zone.undeploy()

    def test_directory_is_dir(self):
        self.assertTrue(self._zone.path.joinpath("directory").is_dir())

    def test_file_content(self):
        with self._zone.path.joinpath("file").open("r") as handle:
            self.assertEqual(handle.read(), "hello-world")

    def test_file2_content(self):
        with self._zone.path.joinpath("file2").open("r") as handle:
            self.assertEqual(handle.read(), "helloworld")

    def test_link_is_symlink(self):
        self.assertTrue(self._zone.path.joinpath("link").is_symlink())

    def test_link_content(self):
        with self._zone.path.joinpath("link").open("r") as handle:
            self.assertEqual(handle.read(), "hello-world")

    def test_link_samefile(self):
        self._zone.path.joinpath("link").samefile(
            self._zone.path.joinpath("file")
        )

    def test_relative_directory_path(self):
        with self.assertRaises(zonys.core.configuration.InvalidConfigurationError):
            self._zone = self._namespace.zone_manager.zones.create(provision=[
                {
                    "directory": {
                        "path": "file",
                    },
                }
            ])

    def test_relative_file_path(self):
        with self.assertRaises(zonys.core.configuration.InvalidConfigurationError):
            self._zone = self._namespace.zone_manager.zones.create(provision=[
                {
                    "file": {
                        "path": "file",
                    },
                }
            ])

    def test_relative_link_source_path(self):
        with self.assertRaises(zonys.core.configuration.InvalidConfigurationError):
            self._zone = self._namespace.zone_manager.zones.create(provision=[
                {
                    "link": {
                        "source": "from",
                        "destination": "/to",
                    },
                }
            ])

    def test_relative_link_destination_path(self):
        with self.assertRaises(zonys.core.configuration.InvalidConfigurationError):
            self._zone = self._namespace.zone_manager.zones.create(provision=[
                {
                    "link": {
                        "source": "/from",
                        "destination": "to",
                    },
                }
            ])

    def test_relative_archive(self):
        with self.assertRaises(zonys.core.configuration.InvalidConfigurationError):
            self._zone = self._namespace.zone_manager.zones.create(provision=[
                {
                    "archive": {
                        "source": "/from",
                        "destination": "http://ftp.freebsd.org/pub/FreeBSD/releases/amd64/13.0-RELEASE/base.txz",
                    },
                }
            ])


if __name__ == "main": # pragma: no cover
    unittest.main()
