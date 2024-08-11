from quiz_enchanter import Plugin, BaseModel

plugin = Plugin.get_plugin("default")
bool_quiz_type = plugin.quiz_type("bool", "Bool")


@bool_quiz_type.model
class BoolModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]
        self.right = json_data["correct"]

        self.selection = None

    def is_correct(self, selection):
        return selection == self.right, 1


@bool_quiz_type.cli
def run(model):
    print(model.question)
    while (selection := input("True (t) or False (f)? ").lower()) not in ("t", "f"):
        pass

    return selection == "t"
