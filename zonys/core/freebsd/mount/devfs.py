import subprocess
import enum

import zonys
import zonys.core
import zonys.core.freebsd
import zonys.core.freebsd.mount


class Mountpoint(zonys.core.freebsd.mount.Mountpoint):
    def mount(self):
        if self.exists():
            raise zonys.core.freebsd.mount.AlreadyExistsError(self)

        command = [
            "mount",
            "-t",
            "devfs",
            "devfs",
            self.destination,
        ]

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        handle = Handle(self.destination)
        handle.rules.hide_all()

        return handle

    def open(self):
        for entry in self._list():
            if entry[1] == str(self.destination) and "devfs" in list(entry[2]):
                return Handle(entry[1])

        raise zonys.core.freebsd.mount.NotExistsError(self)


class Handle(zonys.core.freebsd.mount.Handle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__rules = Rules(self)

    @property
    def rules(self):
        return self.__rules


class Rules:
    def __init__(self, handle):
        self.__handle = handle

    def apply_set(self, number):
        command = [
            "devfs",
            "-m",
            str(self.__handle.destination),
            "rule",
            "-s",
            str(number),
            "applyset",
        ]

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def apply(self, rule):
        if not isinstance(rule, Rule):
            print(rule)
            raise ValueError("rule must be instance of Rule")

        command = [
            "devfs",
            "-m",
            str(self.__handle.destination),
            "rule",
            "apply",
            *str(rule).split(" "),
        ]

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def hide_all(self):
        self.apply(
            Rule(
                None,
                RuleHideAction(),
            )
        )

    def unhide_all(self):
        self.apply(
            Rule(
                None,
                RuleUnhideAction(),
            )
        )

    def unhide_path(self, path):
        self.apply(
            Rule(
                RulePathCondition(path),
                RuleUnhideAction(),
            )
        )


class RuleCondition:
    def __str__(self):
        raise NotImplementedError()


class RulePathCondition(RuleCondition):
    def __init__(self, pattern):
        self.__pattern = pattern

    def __str__(self):
        return "path {}".format(self.pattern)

    @property
    def pattern(self):
        return self.__pattern


class RuleTypeConditionDeviceType(enum.Enum):
    DISK = "disk"
    MEMORY = "mem"
    TAPE = "tape"
    TTY = "tty"


class RuleTypeCondition(RuleCondition):
    def __init__(self, device_type):
        if not isinstance(device_type, RuleTypeConditionDeviceType):
            raise ValueError(
                "device_type must be instance of RuleTypeConditionDeviceType"
            )

        self.__device_type = device_type

    def __str__(self):
        return "type {}".format(self.device_type)

    @property
    def device_type(self):
        return self.__device_type


class RuleAction:
    def __str__(self):
        raise NotImplementedError()


class RuleGroupAction(RuleAction):
    def __init__(self, group_id):
        self.__groud_id = group_id

    def __str__(self):
        return "group {}".format(self.group_id)

    @property
    def group_id(self):
        return self.__group_id


class RuleIncludeAction(RuleAction):
    def __init__(self, ruleset):
        self.__ruleset = ruleset

    def __str__(self):
        return "include {}".format(self.ruleset)

    @property
    def ruleset(self):
        return self.__ruleset


class RuleModeAction(RuleAction):
    def __init__(self, file_mode):
        self.__file_mode = file_mode

    def __str__(self):
        return "mode {}".format(self.file_mode)

    @property
    def file_mode(self):
        return self.__file_mode


class RuleUserAction(RuleAction):
    def __init__(self, user_id):
        self.__user_id = user_id

    def __str__(self):
        return "user {}".format(self.user_id)

    @property
    def user_id(self):
        return self.__user_id


class RuleUnhideAction(RuleAction):
    def __str__(self):
        return "unhide"


class RuleHideAction(RuleAction):
    def __str__(self):
        return "hide"


class Rule:
    def __init__(self, condition, action):
        if condition is not None and not isinstance(condition, RuleCondition):
            raise ValueError("condition must be None or instance of RuleCondition")

        if not isinstance(action, RuleAction):
            raise ValueError("action must be instance of RuleAction")

        self.__condition = condition
        self.__action = action

    def __str__(self):
        result = ""

        if self.condition is not None:
            result = "{} ".format(str(self.condition))

        result = "{}{}".format(result, str(self.action))

        return result

    @property
    def condition(self):
        return self.__condition

    @property
    def action(self):
        return self.__action
