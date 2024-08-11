import enum
import re

from quiz_enchanter import Plugin, BaseModel


plugin = Plugin.get_plugin("default")
match_quiz_type = plugin.quiz_type("match", "Match")


class IsCorrectWhen(enum.IntFlag):
    regex = enum.auto()
    in_correct = enum.auto()
    regex_and_in_correct = regex | in_correct


STRING_TO_IS_CORRECT_WHEN = {
    "regex": IsCorrectWhen.regex,
    "in_correct": IsCorrectWhen.in_correct,
    "regex_and_in_correct": IsCorrectWhen.regex_and_in_correct
}


@match_quiz_type.model
class MatchModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]

        self.strip_start_and_end = json_data.get("strip_start_and_end", True)
        self.ignore_case = json_data.get("ignore_case", False)

        self.regex = json_data.get("regex", None)

        try:
            self.is_correct_when = STRING_TO_IS_CORRECT_WHEN[json_data.get("is_correct_when", "regex_and_in_correct")]
        except (KeyError, IndexError):
            raise KeyError("Invalid data for field 'is_correct_when'!")


        correct = json_data.get("correct", None)
        self.correct = correct if isinstance(correct, list) else [correct]  # Multiple correct answers are allowed!


    def is_correct(self, user_answer):
        if IsCorrectWhen.in_correct in self.is_correct_when:
            striped_selection = user_answer.strip() if self.strip_start_and_end else user_answer

            if self.ignore_case:
                lowercased_correct = [r.lower() for r in self.correct]
                in_correct = striped_selection.lower() in lowercased_correct
            else:
                in_correct = striped_selection in self.correct
        else:
            in_correct = True  # Because the user's answer mustn't be in correct answers

        if IsCorrectWhen.regex in self.is_correct_when and self.regex is not None:
            matches_regex = bool(re.match(self.regex, user_answer))
        else:
            matches_regex = True

        return matches_regex and in_correct, 1


@match_quiz_type.cli
def run(model):
    print(model.question)

    return input("Answer: ")
