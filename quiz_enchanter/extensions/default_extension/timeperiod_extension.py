from isodate import parse_duration

from quiz_enchanter import Plugin, BaseModel

plugin = Plugin.get_plugin("default")
date_period_quiz_type = plugin.quiz_type("timeperiod", "TimePeriod")


@date_period_quiz_type.model
class TimePeriodModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]

        right_field_from_json = json_data["right"]
        right_as_strings = right_field_from_json if isinstance(right_field_from_json, list) else [right_field_from_json]
        # Multiple right answers are allowed!
        self.right = [parse_duration(period_as_string) for period_as_string in right_as_strings]

        self.selection = None

    @property
    def is_right(self):
        return self.selection in self.right, 1


@date_period_quiz_type.cli
def run(model):
    print(model.question)

    while True:
        answer = input("Answer: ")
        try:
            model.selection = parse_duration(answer)
            break
        except ValueError:
            continue

    return model.is_right
