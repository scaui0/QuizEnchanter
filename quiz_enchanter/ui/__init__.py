import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import List

import isodate
import platformdirs
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QDragEnterEvent, QDropEvent, QDragMoveEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedLayout, QListWidget, QFileDialog, QLabel, QDialog
from PyQt6.uic import loadUi
from pydantic import BaseModel as JSONBaseModel

from quiz_enchanter import Quiz, BaseGUI, DictModel, DialogueOptions, response_for_points, __author__, __version__
# noinspection PyUnresolvedReferences
from . import resources


CURRENT_PATH = Path(__file__).parent
QUIZ_PATH = CURRENT_PATH.parent.parent / "quizzes"
UI_FILES_PATH = CURRENT_PATH / "ui_files"

CONFIG_PATH = platformdirs.user_config_path("QuizEnchanter", appauthor=__author__, ensure_exists=True)
LOG_PATH = platformdirs.user_log_path("QuizEnchanter", appauthor=__author__, ensure_exists=True)

PROGRAMMING_MODE = True


def handle_exception(exc_type, exc_value, exc_traceback):
    def to_isoformat_for_filename(value: datetime):
        return isodate.datetime_isoformat(value).replace(":", "-")

    if PROGRAMMING_MODE:
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    else:
        logger = logging.getLogger()
        file_handler = logging.FileHandler(LOG_PATH / f"error-{to_isoformat_for_filename(datetime.now())}.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.exit()


sys.excepthook = handle_exception


def remove_duplicates(seq):
    seen = set()
    result = []
    for x in reversed(seq):
        if x not in seen:
            result.append(x)
            seen.add(x)
    result.reverse()
    return result


def get_common_path(paths):
    paths = [Path(p) for p in paths]

    min_length = min(len(p.parts) for p in paths)

    common_parts = []
    for i in range(min_length):
        part = paths[0].parts[i]

        if all(p.parts[i] == part for p in paths):
            common_parts.append(part)
        else:
            break

    return Path(*common_parts)


class JSONConfig(JSONBaseModel):
    paths: List[Path] = []
    recent_paths: List[Path] = []
    recent_paths_count: int = 10
    show_recent_quizzes: bool = True
    show_paths_from_common_path: bool = True


class Config:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = JSONConfig.model_validate_json(self.config_path.read_text(encoding="utf-8"))

        self.paths: List[Path] = self.config.paths
        self.recent_paths: List[Path] = self.config.recent_paths
        self.recent_paths_count: int = self.config.recent_paths_count
        self.show_recent_quizzes: bool = self.config.show_recent_quizzes
        self.show_paths_from_common_path: bool = self.config.show_paths_from_common_path

    def save(self):
        self.config.paths = self.paths
        self.config.recent_paths_count = self.recent_paths_count
        self.config.show_recent_quizzes = self.show_recent_quizzes
        self.config.show_paths_from_common_path = self.show_paths_from_common_path
        self.config.recent_paths = remove_duplicates(self.recent_paths[-self.recent_paths_count:])

        self.config_path.write_text(self.config.model_dump_json(indent=2), encoding="utf-8")


class ListWidgetFileDrops(QListWidget):
    file_dropped = pyqtSignal(Path)

    def __init__(self, parent):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.file_dropped.emit(Path(file_path))
            event.acceptProposedAction()
        else:
            event.ignore()


class Settings(QDialog):

    def __init__(self, config: Config, set_config_attributes=False):
        super().__init__()
        loadUi(UI_FILES_PATH / "settings.ui", self)

        self.config = config

        paths = config.paths
        recent_paths = config.recent_paths
        show_recent_quizzes = config.show_recent_quizzes
        recent_paths_count = config.recent_paths_count

        self.set_config_attributes = set_config_attributes

        self.add_button.clicked.connect(self.add_clicked)
        self.add_folder_button.clicked.connect(self.add_folder_clicked)
        self.remove_button.clicked.connect(self.remove_clicked)

        self.show_recent_quizzes_checkbox.toggled.connect(self.set_show_recent_quizzes)
        self.recent_quizzes_count.valueChanged.connect(self.set_recent_quizzes_count)
        self.remove_button_recent.clicked.connect(self.remove_recent_button_clicked)
        self.list_widget.file_dropped.connect(self.add_file_or_folder)

        self.show_recent_quizzes_checkbox.setChecked(show_recent_quizzes)
        self.recent_quizzes_count.setValue(recent_paths_count)

        self.list_widget.clear()
        self.recent_quizzes_list_widget.clear()

        self.paths = [] + paths
        self.recent_paths = [] + recent_paths
        self.show_recent_quizzes = show_recent_quizzes
        self.recent_quizzes_count = recent_paths_count

        self.process_path_changes()

    def add_file_or_folder(self, path):
        self.paths.append(path)
        self.process_path_changes()

    def add_clicked(self):
        files = QFileDialog.getOpenFileNames(self)
        as_paths = [Path(file) for file in files[0]]
        self.paths += as_paths

        self.process_path_changes()

    def add_folder_clicked(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.paths.append(Path(folder))
            self.process_path_changes()

    def remove_clicked(self):
        current_index = self.list_widget.currentIndex().row()
        if len(self.paths) != 0:
            del self.paths[current_index]
            self.process_path_changes()

    def process_path_changes(self):
        self.list_widget.clear()
        self.list_widget.addItems(str(path) for path in self.paths)
        self.remove_button.setDisabled(len(self.paths) == 0)

        self.recent_quizzes_list_widget.clear()
        self.recent_quizzes_list_widget.addItems(reversed(
            [str(path) for path in self.recent_paths[:self.recent_quizzes_count]]
        ))
        self.remove_button_recent.setDisabled(len(self.recent_paths) == 0)

    def set_show_recent_quizzes(self, show_recent_quizzes: bool):
        self.show_recent_quizzes = show_recent_quizzes

    def set_recent_quizzes_count(self, value: int):
        self.recent_quizzes_count = value

    def remove_recent_button_clicked(self):
        current_index = self.recent_quizzes_list_widget.currentIndex().row()
        if len(self.recent_paths) != 0:
            del self.recent_paths[current_index]
            self.process_path_changes()

    def accept(self):
        if self.set_config_attributes:
            self.config.paths = self.paths
            self.config.recent_paths = self.recent_paths
            self.config.show_recent_quizzes = self.show_recent_quizzes
            self.config.recent_paths_count = self.recent_quizzes_count

        super().accept()


class QuizSelectWindow(QDialog):
    def __init__(self, config_path):
        super().__init__()
        loadUi(UI_FILES_PATH / "select_quiz.ui", self)

        self.list_widget: QListWidget

        self.common_paths_checkbox.clicked.connect(self.process_changes)
        self.setting_button.clicked.connect(self.open_settings)
        self.open_button.clicked.connect(self.open_quiz_and_accept)
        self.list_widget.doubleClicked.connect(self.set_selected_path_from_selection_in_list_widget)
        self.recent_quizzes_list_widget.doubleClicked.connect(
            self.set_selection_path_from_selection_in_recent_path_list_widget
        )

        self.config_path = config_path
        self.config = Config(self.config_path)

        self.recent_quizzes_label.setVisible(self.config.show_recent_quizzes)
        self.recent_quizzes_list_widget.setVisible(self.config.show_recent_quizzes)

        self.file_paths: List[Path] = []
        self.file_paths_as_strings = []
        self.save_config_changes_on_every_change = True
        self.save_paths_at_end = True
        self.selected_path = None

        self.common_paths_checkbox.setChecked(self.config.show_paths_from_common_path)

        self.update_paths(self.config.paths)

    def update_paths(self, paths):
        self.file_paths = []
        for path in paths:
            if path.is_dir():
                self.add_files_from_folder(path)
            else:
                self.file_paths.append(path)
        self.process_changes()

    def set_selected_path_from_selection_in_list_widget(self, index: QModelIndex):
        self.set_selection(self.file_paths[index.row()])

    def set_selection_path_from_selection_in_recent_path_list_widget(self, index: QModelIndex):
        self.set_selection(tuple(reversed(self.config.recent_paths))[index.row()])

    def set_selection(self, path, append_to_recent=True):
        self.selected_path = path
        if append_to_recent:
            self.config.recent_paths.append(self.selected_path)
        self.process_changes()
        self.accept()

    def add_files_from_folder(self, folder):
        if folder.is_dir():
            for quiz_path in folder.iterdir():
                self.file_paths.append(quiz_path)
            self.process_changes()

    def process_changes(self):
        self.file_paths = list(dict.fromkeys(self.file_paths))

        if len(self.file_paths) != 0:
            if self.common_paths_checkbox.isChecked():
                if len(self.file_paths) == 1:
                    # Extra handling because the single path would be relative to itself, so the result would be "."
                    self.file_paths_as_strings = [str(self.file_paths[0].relative_to(self.file_paths[0].parent))]
                else:
                    common_path = get_common_path(self.file_paths)
                    self.file_paths_as_strings = [str(path.relative_to(common_path)) for path in self.file_paths]
            else:
                self.file_paths_as_strings = list(str(path) for path in self.file_paths)
        else:
            self.file_paths_as_strings = []

        self.recent_quizzes_list_widget.clear()
        recent_paths = self.config.recent_paths
        if len(recent_paths) != 0:
            if self.common_paths_checkbox.isChecked():
                if len(recent_paths) == 1:
                    recent_quizzes_as_strings = ([str(recent_paths[0].relative_to(recent_paths[0].parent))])
                else:
                    common_path = get_common_path(recent_paths)
                    recent_quizzes_as_strings = (str(path.relative_to(common_path)) for path in recent_paths)
            else:
                recent_quizzes_as_strings = (str(path) for path in recent_paths)

            self.recent_quizzes_list_widget.addItems(reversed(list(recent_quizzes_as_strings)))

        if self.save_config_changes_on_every_change:
            self.config.show_paths_from_common_path = self.common_paths_checkbox.isChecked()
            self.config.save()

        self.list_widget.clear()
        self.list_widget.addItems(self.file_paths_as_strings)

    def open_settings(self):
        dialogue = Settings(self.config, set_config_attributes=True)
        if dialogue.exec() == QDialog.DialogCode.Accepted:
            self.update_paths(self.config.paths)

            self.recent_quizzes_label.setVisible(self.config.show_recent_quizzes)
            self.recent_quizzes_list_widget.setVisible(self.config.show_recent_quizzes)

            self.process_changes()

    def open_quiz_and_accept(self):
        raw_path = QFileDialog.getOpenFileName(self, "Open File",
                                               filter="Quiz Files (*.json);;All Files (*)")  # TODO Do it everywhere
        if any(raw_path):
            self.set_selection(Path(raw_path[0]), append_to_recent=False)


HTML_SPAN_WITH_BIG_FONT_SIZE = """
<p>
<span style=" font-size:{size}pt;">
{}
</span>
</p>
"""

HTML_BODY = """
<html><head/><body>
{contents}
</body></html>
"""


class MainWindow(QMainWindow):
    def __init__(self, quiz: Quiz):
        super().__init__()
        loadUi(UI_FILES_PATH / "main.ui", self)

        self.quiz = quiz
        self.current_quiz_index = 0
        self.dialogue_options = DialogueOptions()

        self.reached_points = 0
        self.max_points = 0

        self.check.clicked.connect(self.check_clicked)
        self.quiz_widget_layout = QStackedLayout()
        self.stacked_layout_placeholder.setLayout(self.quiz_widget_layout)

        self.models = []
        for quiz_type, quiz_data in self.quiz.quizzes:
            model = quiz_type.get("model", DictModel)(quiz_data)
            self.models.append(model)
            self.quiz_widget_layout.addWidget(quiz_type.get("gui", BaseGUI)(model))

        self.message_label = QLabel(self)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.quiz_widget_layout.addWidget(self.message_label)

        self.is_message_displayed = False
        self.is_last_message_displayed = False

    def show_widget(self, widget):
        self.quiz_widget_layout.setCurrentWidget(widget)

    def show_next_widget(self):
        self.current_quiz_index += 1
        if self.current_quiz_index >= len(self.models):  # End of quiz

            reached_points = self.reached_points
            max_points = self.max_points

            try:
                percent = reached_points / max_points * 100
            except ZeroDivisionError:
                percent = 100

            message = ""

            if self.dialogue_options.show_rating_at_end:
                message += HTML_SPAN_WITH_BIG_FONT_SIZE.format(
                    response_for_points(reached_points, max_points), size=25
                )

            if self.dialogue_options.show_total:
                message += HTML_SPAN_WITH_BIG_FONT_SIZE.format(
                    f"\nTotal: {int(percent)}% {reached_points}/{max_points}", size=15
                )

            self.show_message(HTML_BODY.format(contents=message))
            self.check.setText("Close")
            self.is_last_message_displayed = True
        else:
            self.quiz_widget_layout.setCurrentIndex(self.current_quiz_index)
            if self.current_quiz_index == len(self.models) - 1:
                self.check.setText("Finish")

    def check_clicked(self):
        if self.is_message_displayed:
            if self.is_last_message_displayed:
                self.close()
            else:
                self.is_message_displayed = False
                self.check.setText("Check")
                self.show_next_widget()
        else:
            reached_points, max_points = self.models[self.current_quiz_index].is_correct(  # get reached and max points
                self.quiz_widget_layout.currentWidget().selection()
            )
            response = self.dialogue_options.get_response_for_question(reached_points, max_points)  # get response)

            self.reached_points += reached_points
            self.max_points += max_points

            if response is not None:
                self.show_message(response)
            else:
                self.show_next_widget()

    def show_message(self, message):
        self.is_message_displayed = True
        self.message_label.setText(message)
        self.quiz_widget_layout.setCurrentWidget(self.message_label)
        self.check.setText("Next")

    def keyPressEvent(self, key: QKeyEvent | None):
        if key.key() == Qt.Key.Key_Return:
            self.check_clicked()


def main(quiz_path=None, create_config_file_if_not_exists=True):
    CONFIG_FILE_PATH = CONFIG_PATH / f"{__version__}-config.json"
    if not CONFIG_FILE_PATH.exists() and create_config_file_if_not_exists:
        CONFIG_FILE_PATH.write_text(JSONConfig().model_dump_json(indent=2), encoding="utf-8")

    app = QApplication([])

    if quiz_path is None:
        dialogue = QuizSelectWindow(CONFIG_FILE_PATH)
        if dialogue.exec() != QDialog.DialogCode.Accepted:
            return
        quiz = Quiz(dialogue.selected_path)
    else:
        quiz = Quiz(quiz_path)

    window = MainWindow(quiz)

    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
