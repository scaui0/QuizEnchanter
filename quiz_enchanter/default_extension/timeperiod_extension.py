from isodate import parse_duration

from quiz_enchanter import Plugin, BaseModel

plugin = Plugin.get_plugin("default")
date_period_quiz_type = plugin.quiz_type("timeperiod", "TimePeriod")


@date_period_quiz_type.model
class TimePeriodModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]

        correct_field_from_json = json_data["correct"]
        correct_as_strings = correct_field_from_json if isinstance(correct_field_from_json, list) else [correct_field_from_json]
        # Multiple correct answers are allowed!
        self.correct = [parse_duration(period_as_string) for period_as_string in correct_as_strings]

    def is_correct(self, selection):
        return selection in self.correct, 1


@date_period_quiz_type.cli
def run(model):
    print(model.question)

    while True:
        answer = input("Answer: ")
        try:
            return parse_duration(answer)
        except ValueError:
            continue
