#!usr/bin/env python3
import logging
from argparse import ArgumentParser
from pathlib import Path

from quiz_enchanter import execute_quiz_as_cli_from_quiz_file


CURRENT_PATH = Path(__file__).parent

QUIZ_ALWAYS_TO_OPEN = None

parser = ArgumentParser("QuizEnchanter", description="A quiz program")
parser.add_argument("file", nargs='?', help="optional, absolute path to a quiz file")
parser.add_argument("-d", "--debug", action='store_true', help="print debug messages")

args = parser.parse_args()

if args.debug:
    logging.basicConfig(
        level= logging.DEBUG,
        format="[%(levelname)s][%(asctime)s](%(name)s) - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )
else:
    logging.basicConfig(
        level= logging.FATAL,
        format="[%(levelname)s][%(asctime)s](%(name)s) - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )

logger = logging.getLogger(__name__)

quiz_path = args.file
if QUIZ_ALWAYS_TO_OPEN is not None:
    quiz_path = QUIZ_ALWAYS_TO_OPEN
    logger.info(f"Loaded quiz from file {QUIZ_ALWAYS_TO_OPEN} because QUIZ_ALWAYS_TO_OPEN contains this path.")

elif quiz_path is None:
    quiz_name = input("Quiz file (in quizzes folder): ")
    quiz_path = CURRENT_PATH / f"quizzes/{quiz_name}"
    logger.info(f"Loaded quiz file from {quiz_path}")

execute_quiz_as_cli_from_quiz_file(quiz_path)
