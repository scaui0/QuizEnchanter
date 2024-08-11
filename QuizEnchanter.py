#!usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path

from quiz_enchanter import execute_quiz_as_cli_from_quiz_file, path_relative_or_absolute


CURRENT_PATH = Path(__file__).parent

QUIZ_ALWAYS_TO_OPEN_IF_NO_OTHER_SPECIFIED = None

parser = ArgumentParser("QuizEnchanter", description="A quiz program that allows you to create plugins")
parser.add_argument(
    "file", nargs='?',
    help="optional, absolute path to a quiz file or a relative path starts from quizzes folder"
)

args = parser.parse_args()

if args.file is not None:
    quiz_path = path_relative_or_absolute(Path(args.file), CURRENT_PATH / "quizzes")
elif QUIZ_ALWAYS_TO_OPEN_IF_NO_OTHER_SPECIFIED is not None:
    quiz_path = path_relative_or_absolute(Path(QUIZ_ALWAYS_TO_OPEN_IF_NO_OTHER_SPECIFIED), CURRENT_PATH / "quizzes")
    print(
        f"Loaded quiz from file {QUIZ_ALWAYS_TO_OPEN_IF_NO_OTHER_SPECIFIED} because QUIZ_ALWAYS_TO_OPEN contains this "
        f"path."
    )
else:
    quiz_name = input("Quiz file (in quizzes folder): ")
    quiz_path = path_relative_or_absolute(Path(quiz_name), CURRENT_PATH / "quizzes")

execute_quiz_as_cli_from_quiz_file(quiz_path)
