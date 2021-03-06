import collections
import os
import pathlib
import sys
import typing

import cerberus
import toolz

import zonys
import zonys.core
import zonys.core.collection


class Error(RuntimeError):
    pass


class InvalidConfigurationError(Error):
    pass


cerberus.Validator.types_mapping["type"] = cerberus.TypeDefinition("type", (type,), ())


class Validator(cerberus.Validator):
    def __init__(self, *args, **kwargs):
        self.handler_details = kwargs.get("handler_details")

        super().__init__(*args, **kwargs)

        if isinstance(self.error_handler, cerberus.errors.ToyErrorHandler):
            self.error_handler = cerberus.errors.BasicErrorHandler()

    def _validate_handler(self, handler, _field, value):
        """
        {'type':'type'}
        """
        if (
            not isinstance(self.error_handler, cerberus.errors.ToyErrorHandler)
            and len(self.errors) == 0
        ):
            self.handler_details.append(ValidationContextHandlerDetail(handler, value))


class VariableAccessor:
    def __init__(self, data: typing.Any):
        self.__data = data

    def __getattr__(self, name: typing.Any) -> typing.Any:
        if self.__data is None:
            return None

        return VariableAccessor(self.__data.get(name))

    def __str__(self) -> str:
        return str(self.__data)


class ValidationContextHandlerDetail:
    def __init__(self, handler, configuration):
        self.__handler = handler
        self.__configuration = configuration

    @property
    def handler(self):
        return self.__handler

    @property
    def configuration(self):
        return self.__configuration


class Manager:
    def __init__(self, *args, **kwargs):
        self.__rollback_methods = collections.OrderedDict()
        self.__attached_handlers = set()
        self.__commit_handlers = []
        self.__variables = {}

        for (key, value) in kwargs.items():
            setattr(self, key, value)

    def read(
        self,
        schemas,
        configuration,
        base: typing.Optional[pathlib.Path] = None,
    ):
        if base is None:
            base = pathlib.Path(os.getcwd())

        current_configuration = {
            **configuration,
        }

        for schema in schemas:
            validator = Validator(allow_unknown=True, handler_details=[])

            if not validator.validate(current_configuration, schema):
                raise InvalidConfigurationError(validator.errors)

            for handler_detail in validator.handler_details:
                handler = handler_detail.handler
                if handler_detail.handler not in self.__attached_handlers:
                    handler_detail.handler.on_attach(
                        AttachEvent(
                            self, handler_detail.configuration, configuration, base
                        )
                    )

                    self.__attached_handlers.add(handler_detail.handler)

                handler.before_configuration(
                    BeforeConfigurationEvent(
                        self,
                        handler_detail.configuration,
                        configuration,
                        base,
                        schemas,
                    )
                )

                self.__commit_handlers.append(
                    (
                        handler,
                        handler_detail.configuration,
                        configuration,
                        base,
                    )
                )

                handler.after_configuration(
                    AfterConfigurationEvent(
                        self,
                        handler_detail.configuration,
                        configuration,
                        base,
                        schemas,
                    )
                )

    @property
    def commit_handlers(self) -> typing.List["Handler"]:
        return self.__commit_handlers

    @property
    def variables(self):
        return self.__variables

    def commit(self, __name, **kwargs):
        name = __name

        on_commit_method_name = "on_commit_{}".format(name)
        on_rollback_method_name = "on_rollback_{}".format(name)

        for (
            instance,
            options,
            configuration,
            base,
        ) in self.__commit_handlers:
            if not hasattr(instance, on_commit_method_name):
                continue

            commit = getattr(instance, on_commit_method_name)
            if not callable(commit):
                continue

            def format_value(value):
                result = None

                if isinstance(value, dict):
                    result = toolz.valmap(format_value, value)
                elif isinstance(value, list):
                    result = list(map(format_value, value))
                elif isinstance(value, bool):
                    result = value
                elif hasattr(value, "format") and callable(value.format):
                    result = value.format(
                        env=dict(os.environ),
                        environment=dict(os.environ),
                        **toolz.valmap(
                            VariableAccessor,
                            self.__variables,
                        ),
                    )
                else:
                    result = value

                return result

            options = format_value(options)

            normalize_event = NormalizeEvent(
                self,
                options,
                configuration,
                base,
                kwargs,
            )
            instance.on_normalize(normalize_event)

            commit_event = CommitEvent(
                self,
                options,
                configuration,
                base,
                kwargs,
                normalize_event.normalized,
            )
            commit(commit_event)

            if hasattr(instance, on_rollback_method_name):
                if name not in self.__rollback_methods:
                    self.__rollback_methods[name] = []

                rollback = getattr(instance, on_rollback_method_name)
                rollback_event = RollbackEvent(
                    self,
                    options,
                    configuration,
                    base,
                    kwargs,
                    normalize_event.normalized,
                )
                self.__rollback_methods[name].append(lambda: rollback(rollback_event))

            kwargs = commit_event.context

        return kwargs

    def rollback(self):
        for steps in reversed(self.__rollback_methods.values()):
            for rollback in steps:
                rollback()

        self.__rollback_methods = collections.OrderedDict()


class Event:
    def __init__(self, manager, options, configuration, base: pathlib.Path):
        self.__manager = manager
        self.__options = options
        self.__configuration = configuration
        self.__base = base

    @property
    def manager(self) -> "Manager":
        return self.__manager

    @property
    def options(self):
        return self.__options

    @property
    def configuration(self):
        return self.__configuration

    @property
    def base(self) -> pathlib.Path:
        return self.__base


class AttachEvent(Event):
    pass


class TransactionEvent(Event):
    # pylint: disable=too-many-arguments
    def __init__(
        self, manager, options, configuration, base: pathlib.Path, context, normalized
    ):
        super().__init__(manager, options, configuration, base)

        self.__context = context
        self.__normalized = normalized

    @property
    def context(self):
        return self.__context

    @property
    def normalized(self):
        return self.__normalized


class CommitEvent(TransactionEvent):
    pass


class RollbackEvent(TransactionEvent):
    pass


class ConfigurationEvent(Event):
    def __init__(self, manager, options, configuration, base: pathlib.Path, schemas):
        super().__init__(manager, options, configuration, base)
        self.__schemas = schemas

    @property
    def schemas(self):
        return self.__schemas


class BeforeConfigurationEvent(ConfigurationEvent):
    pass


class AfterConfigurationEvent(ConfigurationEvent):
    pass


class NormalizeEvent(Event):
    def __init__(self, manager, options, configuration, base: pathlib.Path, context):
        super().__init__(manager, options, configuration, base)

        self.__context = context
        self.__normalized = {}

    @property
    def context(self):
        return self.__context

    @property
    def normalized(self):
        return self.__normalized


class Handler:
    @staticmethod
    def on_normalize(event):
        pass

    @staticmethod
    def on_attach(event):
        pass

    @staticmethod
    def before_configuration(
        event: "BeforeConfigurationEvent",
    ):
        pass

    @staticmethod
    def after_configuration(
        event: "AfterConfigurationEvent",
    ):
        pass
