from datetime import datetime

from quiz_enchanter import Plugin, BaseModel

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
        return selection in self.correct, 1


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
