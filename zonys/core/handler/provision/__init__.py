from zonys.core.handler.provision import (
    archive,
    command,
    directory,
    file,
    git,
    link,
    package,
    path,
    user,
)

SCHEMA = {
    "provision": {
        "type": "list",
        "schema": {
            "anyof": [
                archive.SCHEMA,
                command.SCHEMA,
                directory.SCHEMA,
                file.SCHEMA,
                git.SCHEMA,
                link.SCHEMA,
                package.SCHEMA,
                path.SCHEMA,
                user.SCHEMA,
            ],
        },
    },
}
