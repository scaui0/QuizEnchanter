from datetime import datetime

from quiz_enchanter import Plugin, BaseModel

plugin = Plugin.get_plugin("default")
datetime_quiz_type = plugin.quiz_type("datetime", "DateTime")


BASIC_ISO_8601_FORMAT = "YYYY-MM-DDThh:mm:ss"


@datetime_quiz_type.model
class DateTimeModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]
        right_from_json = json_data["right"]

        right_datetimes_as_strings = right_from_json if isinstance(right_from_json, list) else [right_from_json]
        # Multiple right are allowed
        self.right = [datetime.fromisoformat(datetime_string) for datetime_string in right_datetimes_as_strings]

        self.show_format_information = json_data.get("show_format_information", True)

        self.selection = None

    @property
    def is_right(self):
        return self.selection in self.right, 1


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
            model.selection = datetime.fromisoformat(answer)
            break
        except ValueError:
            continue

    return model.is_right
