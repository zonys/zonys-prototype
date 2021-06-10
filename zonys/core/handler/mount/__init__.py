from zonys.core.handler.mount import (
    devfs,
    nullfs,
    zfs,
)

SCHEMA = {
    "mount": {
        "type": "list",
        "schema": {
            "anyof": [
                devfs.SCHEMA,
                nullfs.SCHEMA,
                zfs.SCHEMA,
            ],
        },
    },
}
