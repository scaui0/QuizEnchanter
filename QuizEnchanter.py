#!usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path

from quiz_enchanter import path_relative_or_absolute, Quiz, DialogueOptions


CURRENT_PATH = Path(__file__).parent

QUIZ_ALWAYS_TO_OPEN_IF_NO_OTHER_SPECIFIED = None


def run_cli(quiz_path=None):
    if quiz_path is None:
        quiz_path = path_relative_or_absolute(Path(input("Quiz file in quizzes folder or absolute path: ")),
                                              CURRENT_PATH / "quizzes")

    Quiz(quiz_path).run_cli(DialogueOptions())


def main():
    parser = ArgumentParser("QuizEnchanter", description="A quiz program that allows you to create plugins")
    parser.add_argument(
        "file", nargs='?',
        help="optional, absolute path to a quiz file or a relative path starts from quizzes folder"
    )
    group = parser.add_mutually_exclusive_group(

    )
    group.add_argument(
        "-g", "--gui", help="Open GUI", action="store_true", default=True
    )
    group.add_argument(
        "-c", "--cli", help="Open CLI", action="store_true"
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
        quiz_path = None

    if args.cli:
        run_cli(quiz_path)
    elif args.gui:
        from quiz_enchanter.ui import main
        main(quiz_path)

if __name__ == '__main__':
    main()
