from datetime import datetime
from pathlib import Path

import isodate.isodatetime
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import QWidget, QDateTimeEdit
from PyQt6.uic import loadUi

from quiz_enchanter import Plugin, BaseModel, BaseGUI


plugin = Plugin.get_plugin("default")
datetime_quiz_type = plugin.quiz_type("datetime", "DateTime")


BASIC_ISO_8601_FORMAT = "YYYY-MM-DDThh:mm:ss"


@datetime_quiz_type.model
class DateTimeModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]
        correct_from_json = json_data["correct"]

        correct_datetimes_as_strings = correct_from_json if isinstance(correct_from_json, list) else [correct_from_json]
        # Multiple correct answers are allowed
        self.correct = [datetime.fromisoformat(datetime_string) for datetime_string in correct_datetimes_as_strings]

        self.show_format_information = json_data.get("show_format_information", True)

    def is_correct(self, selection):
        return int(selection in self.correct), 1


@datetime_quiz_type.cli
def run(model):
    if model.show_format_information:
        print(model.question)
        print(f"Answer's format is ISO 8601. Basic format: {BASIC_ISO_8601_FORMAT}")
    else:
        print(model.question)

    while True:
        answer = input("Answer: ")
        try:
            return datetime.fromisoformat(answer)
        except ValueError:
            continue


@datetime_quiz_type.gui
class DateTimeGUI(BaseGUI):
    def __init__(self, model):
        super().__init__(model)
        loadUi(Path(__file__).parent.parent / "ui/ui_files/datetime.ui", self)

        self.question.setText(model.question)

    def selection(self):
        return self.date_time.dateTime().toPyDateTime()
