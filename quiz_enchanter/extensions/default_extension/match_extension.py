import enum
import re

from quiz_enchanter import Plugin, BaseModel


plugin = Plugin.get_plugin("default")
match_quiz_type = plugin.quiz_type("match", "Match")


class IsRightWhen(enum.IntFlag):
    regex = enum.auto()
    in_right = enum.auto()
    regex_and_in_right = regex | in_right


STRING_TO_IS_RIGHT_WHEN = {
    "regex": IsRightWhen.regex,
    "in_right": IsRightWhen.in_right,
    "regex_and_in_right": IsRightWhen.regex_and_in_right
}


@match_quiz_type.model
class MatchModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]

        self.strip_start_and_end = json_data.get("strip_start_and_end", True)
        self.ignore_case = json_data.get("ignore_case", False)

        self.regex = json_data.get("regex", None)

        try:
            self.is_right_when = STRING_TO_IS_RIGHT_WHEN[json_data.get("is_right_when", "regex_and_in_right")]
        except (KeyError, IndexError):
            raise KeyError("Invalid data for field 'is_right_when'!")


        right = json_data.get("right", None)
        self.right = right if isinstance(right, list) else [right]  # Multiple right answers are allowed!

        self.selection = None

    @property
    def is_right(self):
        if IsRightWhen.in_right in self.is_right_when:
            striped_selection = self.selection.strip() if self.strip_start_and_end else self.selection

            if self.ignore_case:
                lowercased_right = [r.lower() for r in self.right]
                in_right = striped_selection.lower() in lowercased_right
            else:
                in_right = striped_selection in self.right
        else:
            in_right = True  # Because user's answer mustn't be in right answers

        if IsRightWhen.regex in self.is_right_when and self.regex is not None:
            matches_regex = bool(re.match(self.regex, self.selection))
        else:
            matches_regex = True

        return matches_regex and in_right, 1


@match_quiz_type.cli
def run(model):
    print(model.question)
    model.selection = input("Answer: ")

    return model.is_right
