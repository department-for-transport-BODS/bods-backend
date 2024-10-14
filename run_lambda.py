import importlib
import importlib.util
import sys
from sqlalchemy import asc, select

sys.path.append("./src/boilerplate")

from common import BodsDB

db = BodsDB()
Checks = db.classes.avl_cavldataarchive
lambdas = {
    "1": "app",
    "2": "create_sirivm_zip",
    "3": "create_gtfsrt_zip",
}
lambdas.update({"all": "all"})


from json import dumps
import argparse


class Context:
    def get_remaining_time_in_millis(self):
        return 135000


def run_lambda_func(lambda_name):
    print(f"Lambda Executing: {lambda_name}")
    print(f"lambda name: {lambda_name} being executed")
    module_path = f"src.backend.{lambda_name}"

    if importlib.util.find_spec(module_path):
        module = importlib.import_module(module_path)
    else:
        print(f"select lambda module not found {module_path} executing app")
        module = importlib.import_module("src.backend.app")

    lambda_handler = module.lambda_handler
    print(f"Running the lambda: {module_path}::lambda_handler")
    lambda_handler(
        event={},
        context=Context(),
    )


def main():
    """
    Run lambda functions manually
    Command line example:
    python run_lambda.py
    """

    print("Here is the lamda list::::")

    for key, val in lambdas.items():
        print(f"{key}: {val}")

    module_input = input("Choose the module from the above list ")

    # run for all lambdas
    if module_input == "all":
        lambdas.pop("all")
        for lambda_name, _ in lambdas.items():
            run_lambda_func(lambda_name)
    else:
        module_input = str(module_input) if module_input.isdigit() else "0"
        lambda_name = lambdas.get(module_input, None)
        if lambda_name:
            run_lambda_func(lambda_name)
        else:
            print("Please select lambda function from the list")


if __name__ == "__main__":
    main()
