from quiz_enchanter import Plugin, BaseModel

plugin = Plugin.get_plugin("default")
select_quiz_type = plugin.quiz_type("select", "Select")


@select_quiz_type.model
class SelectModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]
        self.options = json_data["options"]

        right = json_data.get("right", None)
        self.right = right if isinstance(right, list) else [right]  # Multiple right answers are allowed!

        self.selection = None

    @property
    def is_right(self):
        return self.selection in self.right, 1


@select_quiz_type.cli
def run(model):
    print(model.question)

    for i, option in enumerate(model.options):
        print(f"[{i+1}]", option)  # +1 because in the CLI it starts counting from 1

    while True:
        selection = input("Select index: ")
        try:
            selection = int(selection) - 1  # -1 because in quiz files they're start counting beginning from 0
            if selection in range(len(model.options)):
                model.selection = selection
                break
        except ValueError:
            pass

    return model.is_right
