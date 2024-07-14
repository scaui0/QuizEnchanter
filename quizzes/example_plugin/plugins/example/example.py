from quiz_enchanter import Plugin, BaseModel


plugin = Plugin("example", "Example plugin")  # The id must match the id from the config file
example_quiz_type = plugin.quiz_type("example", "Example quiz type")


@example_quiz_type.model
class ExampleModel(BaseModel):
    def __init__(self, json_data):
        self.question = json_data["question"]

    @property
    def is_right(self):
        return 1, 1


@example_quiz_type.cli
def run(model):
    input(model.question)

    return model.is_right
