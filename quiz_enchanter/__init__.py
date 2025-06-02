__version__ = '2.0.0'
__author__ = '_Scaui'

import dataclasses
import json
import random
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from typing import Self

from PyQt6.QtWidgets import QWidget


CURRENT_PATH = Path(__file__).parent
DEFAULT_EXTENSION_PATH = CURRENT_PATH / "default_extension"


def path_relative_or_absolute(path: Path, path_start: Path):
    """Converts a relative or absolute path to an absolute path.

    When an absolute path must be joined, it joins path_start and path.

    :param path_start:
    :param path: The relative or absolute path of the path.
    :return: The input path, converted to an absolute path.
    """
    path = Path(path)
    return path if path.is_absolute() else path_start / path


class AlreadyRegisteredError(BaseException):
    """AlreadyRegisteredError"""

    def __init__(self, thing, type_=None):
        self.type_ = thing.__class__.__name__ if type_ is None else type_
        self.thing = thing

    def __str__(self):
        return f"{self.type_} {self.thing!r} is already registered!"


class NotRegisteredError(BaseException):
    """NotRegisteredError"""

    def __init__(self, thing, type_=None):
        self.type_ = thing.__class__.__name__ if type is None else type_
        self.thing = thing

    def __str__(self):
        return f"{self.type_} {self.thing!r} is not registered!"


class BaseModel:
    def is_correct(self, user_answer):
        return 0, 0


def base_cli(model):
    """
    The default CLI for quizzes

    Returns a tuple of two ints: the reached points and the maximal points the user could reach
    """
    return 0, 0


class BaseGUI(QWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)

    def selection(self):
        return None


class DictModel(dict, BaseModel):
    pass


@dataclasses.dataclass
class DialogueOptions:
    show_rating_at_end: bool = dataclasses.field(default=True)
    show_total: bool = dataclasses.field(default=True)
    show_rating_after_answer: bool = dataclasses.field(default=True)
    show_points_after_answer: bool = dataclasses.field(default=True)
    use_right_wrong_rating_on_true_false_questions: bool = dataclasses.field(default=True)
    show_rating_on_empty_questions: bool = dataclasses.field(default=False)
    print_greeting: bool = dataclasses.field(default=True)

    def get_response_for_question(self, reached_points: int, max_points: int) -> str:
        if (reached_points in (0, 1) and max_points == 1
                and self.use_right_wrong_rating_on_true_false_questions):
            return "That's correct! :)" if reached_points else "That's incorrect! :("
        elif reached_points == 0 and max_points == 0 and not self.show_rating_on_empty_questions:
            pass
        else:
            return (response_for_points(
                reached_points, max_points, SMILEY_RESPONSES
            ) if self.show_rating_after_answer else "" +
                                                    f"{reached_points}/{max_points}" if self.show_points_after_answer else "")


class QuizType:
    def __init__(self, name, identifier, **kwargs):
        self.name = name
        self.identifier = identifier

        self._values = kwargs

    def get(self, value, default=None):
        try:
            return self._values[value]
        except KeyError:
            if default is not None:
                return default
            else:
                raise

    def __getattr__(self, item):
        def decorator(func_or_class):
            self._values[item] = func_or_class

        return decorator

    def __repr__(self):
        return f"<QuizType {self.identifier}>"


class Quiz:
    def __init__(self, main_path):
        main_path = Path(main_path)
        plugin_folders = [DEFAULT_EXTENSION_PATH]

        if main_path.is_dir():
            path_to_quiz_file = main_path / "quiz.json"

            plugin_main_path = main_path / "plugins"
            if plugin_main_path.exists():
                plugin_folders += plugin_main_path.iterdir()
        else:
            path_to_quiz_file = main_path

        plugin_manager = PluginManager()

        for plugin_path in plugin_folders:
            plugin_manager.add_plugin(
                Plugin.plugin_from_main_folder(plugin_path),
                activate=True
            )

        if not path_to_quiz_file.exists():
            raise FileNotFoundError(f"Quiz file does not exist! {path_to_quiz_file}")

        with path_to_quiz_file.open("r", encoding="utf-8") as quiz_file:
            json_data = json.load(quiz_file)

        self.name = json_data["name"]
        self.quizzes = [
            (plugin_manager.all_activated_quiz_types[data["type"]], data) for data in json_data["quizzes"]
        ]

    def run_cli(self, dialogue_options: DialogueOptions):

        if dialogue_options.print_greeting:
            print(f"Welcome to {self.name!r}!\nPlease answer the following questions!\n")

        reached_points = 0
        max_points = 0
        for quiz_type, quiz_data in self.quizzes:
            cli = quiz_type.get("cli", base_cli)
            model = quiz_type.get("model", DictModel)(quiz_data)

            reached_points_for_quiz, max_points_for_quiz = model.is_correct(cli(model))

            reached_points += reached_points_for_quiz
            max_points += max_points_for_quiz

            print(
                dialogue_options.get_response_for_question(reached_points_for_quiz, max_points_for_quiz)
            )

            print()

        try:
            percent = reached_points / max_points * 100
        except ZeroDivisionError:
            percent = 100

        if dialogue_options.show_rating_at_end:
            print(response_for_points(reached_points, max_points))

        if dialogue_options.show_total:
            print(f"Total: {int(percent)}% {reached_points}/{max_points}")

        return reached_points, max_points, percent


class Plugin:
    GLOBAL_PLUGINS = {}

    def __init__(self, identifier, name):
        self.identifier = identifier
        self.name = name
        self.quiz_types = {}

        # if identifier in Plugin.GLOBAL_PLUGINS:
        #     raise AlreadyRegisteredError(identifier, "Plugin")

        Plugin.GLOBAL_PLUGINS[identifier] = self

        if Plugin.GLOBAL_PLUGINS["default"] is None:
            Plugin.plugin_from_main_folder(DEFAULT_EXTENSION_PATH)

    @classmethod
    def get_plugin(cls, identifier: str) -> Self:
        if identifier not in Plugin.GLOBAL_PLUGINS:
            raise NotRegisteredError(identifier, "plugin")
        else:
            return Plugin.GLOBAL_PLUGINS[identifier]

    def register_quiz_type(self, identifier, name, **kwargs):
        if identifier in self.quiz_types:
            raise AlreadyRegisteredError(identifier)
        else:
            self.quiz_types[identifier] = QuizType(
                name=name,
                identifier=identifier,
                **kwargs
            )

    def quiz_type(self, identifier, name):
        if identifier in self.quiz_types:
            return self.quiz_types[identifier]
        else:
            quiz_type = QuizType(name, identifier)
            self.quiz_types[identifier] = quiz_type
            return quiz_type

    @classmethod
    def plugin_from_main_folder(cls, path_to_main_folder: Path):
        """
        Load a plugin from the main folder. This requires that there is a file called 'extension.json'.
        The plugin is added to Plugin.GLOBAL_PLUGINS"""
        with (path_to_main_folder / "extension.json").open(encoding="utf-8") as plugin_config_file:
            plugin_config = json.load(plugin_config_file)

            plugin_id = plugin_config["id"]

            plugin_python_files = (path_to_main_folder / file_name for file_name in plugin_config["files"])

            for plugin_python_file in plugin_python_files:
                # Load plugin_python_file as a module into extension_modul
                spec = spec_from_file_location(plugin_python_file.stem, plugin_python_file)
                extension_modul = module_from_spec(spec)
                # Execute modul
                spec.loader.exec_module(extension_modul)  # Here the plugin registers itself.

        if plugin_id not in Plugin.GLOBAL_PLUGINS:
            raise NotRegisteredError(plugin_id, "Plugin")
        return Plugin.GLOBAL_PLUGINS[plugin_id]  # The Plugin is already registered. It registers itself on creation


class PluginManager:
    """Manager to manage plugins."""

    def __init__(self, activated_plugins=None, deactivated_plugins=None):
        if deactivated_plugins is None:
            deactivated_plugins = {}
        self.deactivated_plugins = deactivated_plugins

        if activated_plugins is None:
            activated_plugins = {}
        self.activated_plugins = activated_plugins

    def activate_plugin(self, plugin_id):
        """Activate the plugin whose identifier is equals to plugin_id."""
        if plugin_id in self.deactivated_plugins:
            self.activated_plugins[plugin_id] = self.deactivated_plugins.pop(plugin_id)
            # Move from activated to deactivated plugins

        elif plugin_id in Plugin.GLOBAL_PLUGINS:
            self.activated_plugins[plugin_id] = Plugin.GLOBAL_PLUGINS[plugin_id]

    def deactivate_plugin(self, plugin_id):
        """Deactivate the plugin whose identifier is equals to plugin_id."""
        if plugin_id in self.activated_plugins:
            self.deactivated_plugins[plugin_id] = self.activated_plugins.pop(plugin_id)
            # Move from deactivated to activated plugins

        elif plugin_id in Plugin.GLOBAL_PLUGINS:
            self.deactivated_plugins[plugin_id] = Plugin.GLOBAL_PLUGINS[plugin_id]

    def remove_plugin(self, plugin_id):
        """Remove the plugin, whose plugin_id is equals to plugin_id."""
        if plugin_id in self.activated_plugins:
            del self.activated_plugins[plugin_id]

        elif plugin_id in self.deactivated_plugins:
            del self.deactivated_plugins[plugin_id]

    def add_plugin(self, plugin, activate=False):
        """Add a Plugin. If the activate flag is set, the plugin will be activated."""
        if activate:
            self.activated_plugins[plugin.identifier] = plugin
        else:
            self.deactivated_plugins[plugin.identifier] = plugin

    @property
    def all_plugins(self) -> dict[str, Plugin]:
        return self.activated_plugins | self.deactivated_plugins

    @property
    def all_activated_quiz_types(self):
        """All quiz types of all activated plugins"""
        return {
            identifier: quiz_type
            for plugin in self.activated_plugins.values()
            for identifier, quiz_type in plugin.quiz_types.items()
        }

    @classmethod
    def plugins_from_main_folder(cls, path_to_main_folder: Path):
        plugin_main_path = path_to_main_folder / "plugins"

        plugin_folders = []
        plugin_manager = PluginManager()
        if plugin_main_path.exists():
            plugin_folders += plugin_main_path.iterdir()

            for plugin_path in plugin_folders:
                plugin_manager.add_plugin(
                    Plugin.plugin_from_main_folder(plugin_path),
                    activate=True
                )
            return plugin_manager


RESPONSES = (
    ("Perfect! :)", "Keep it up! :)"),
    ("You can do it better!",),
    ("You'll learn it!", "Don't give up!", "You'll make it!"),
    ("Everybody can learn it! You can it too!",)
)

SMILEY_RESPONSES = (
    (":)",),
    (":\\", ":/"),
    (":|",),
    (":(",)
)


def response_for_points(points, max_points, responses=None) -> str:
    if responses is None:
        responses = RESPONSES

    if points == max_points:
        return random.choice(responses[0])

    number_of_different_responses = len(responses[1:]) - 1

    for i, response in enumerate(reversed(responses[1:])):
        max_points_for_this_response = (max_points // number_of_different_responses) * i
        if points <= max_points_for_this_response:
            return random.choice(response)
