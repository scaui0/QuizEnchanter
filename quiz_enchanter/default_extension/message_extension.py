from pathlib import Path

from PyQt6.uic import loadUi

from quiz_enchanter import Plugin, BaseModel, BaseGUI


plugin = Plugin.get_plugin("default")
message_quiz_type = plugin.quiz_type("message", "Message")


@message_quiz_type.model
class BoolModel(BaseModel):
    def __init__(self, json_data):
        self.message = json_data["message"]

    def is_correct(self, selection):
        return 0, 0


@message_quiz_type.cli
def run(model):
    input(model.message)


@message_quiz_type.gui
class MessageGUI(BaseGUI):
    def __init__(self, model):
        super().__init__(model)
        loadUi(Path(__file__).parent.parent / "ui/ui_files/message.ui", self)

        self.question.setText(model.message)
