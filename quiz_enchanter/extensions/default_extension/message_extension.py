from quiz_enchanter import Plugin, BaseModel

plugin = Plugin.get_plugin("default")
message_quiz_type = plugin.quiz_type("message", "Message")


@message_quiz_type.model
class BoolModel(BaseModel):
    def __init__(self, json_data):
        self.message = json_data["message"]

    @property
    def is_right(self):
        return 0, 0


@message_quiz_type.cli
def run(model):
    input(model.message)

    return model.is_right
