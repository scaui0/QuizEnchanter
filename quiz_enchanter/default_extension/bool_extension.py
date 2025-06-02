from pathlib import Path

from PyQt6.uic import loadUi

from quiz_enchanter import Plugin, BaseModel, BaseGUI


plugin = Plugin.get_plugin("default")
bool_quiz_type = plugin.quiz_type("bool", "Bool")


@bool_quiz_type.model
class BoolModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]
        self.correct = json_data["correct"]

        self.selection = None

    def is_correct(self, selection):
        return int(selection == self.correct), 1


@bool_quiz_type.cli
def run(model):
    print(model.question)
    while (selection := input("True (t) or False (f)? ").lower()) not in ("t", "f"):
        pass

    return selection == "t"


@bool_quiz_type.gui
class BoolGUI(BaseGUI):
    def __init__(self, model):
        super().__init__(model)
        loadUi(Path(__file__).parent.parent / "ui/ui_files/bool.ui", self)

        self.question.setText(model.question)

    def selection(self):
        return self.true_2.isChecked()
