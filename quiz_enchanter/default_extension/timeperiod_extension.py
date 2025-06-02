from pathlib import Path

from PyQt6.QtWidgets import QSpinBox
from PyQt6.uic import loadUi
from isodate import parse_duration

from quiz_enchanter import Plugin, BaseModel, BaseGUI


plugin = Plugin.get_plugin("default")
time_period_quiz_type = plugin.quiz_type("timeperiod", "TimePeriod")


@time_period_quiz_type.model
class TimePeriodModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]

        correct_field_from_json = json_data["correct"]
        correct_as_strings = correct_field_from_json if isinstance(correct_field_from_json, list) else [correct_field_from_json]
        # Multiple correct answers are allowed!
        self.correct = [parse_duration(period_as_string) for period_as_string in correct_as_strings]

    def is_correct(self, selection):
        return int(selection in self.correct), 1


@time_period_quiz_type.cli
def run(model):
    print(model.question)

    while True:
        answer = input("Answer: ")
        try:
            return parse_duration(answer)
        except ValueError:
            continue


@time_period_quiz_type.gui
class TimePeriodGUI(BaseGUI):
    def __init__(self, model):
        super().__init__(model)
        loadUi(Path(__file__).parent.parent / "ui/ui_files/timeperiod.ui", self)

        self.question.setText(model.question)

    def selection(self):
        years = self.years.value()
        months = self.months.value()
        days = self.days.value()

        hours = self.hours.value()
        minutes = self.minutes.value()
        seconds = self.seconds.value()
        return parse_duration(f"P{years}Y{months}M{days}DT{hours}H{minutes}M{seconds}S")
