"""
The AWS Lambda environment expects each lambda, and layer, to have a requirements.txt
However, we're using poetry to manage our dependencies.

This script will export the requirements.txt files to each lambda/layer folder based on 
the poetry dependency groups defined in pyproject.toml
"""

import subprocess
import tomllib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"
LAMBDA_BASE_DIR = ROOT_DIR / "src/timetables_etl"
BOILERPLATE_LAYER_DIR = ROOT_DIR / "src/boilerplate"


def get_dependency_groups() -> set[str]:
    """
    Get all poetry dependency groups from pyproject.toml
    """
    with open(PYPROJECT_PATH, "rb") as f:
        pyproject = tomllib.load(f)
        return set(pyproject.get("tool", {}).get("poetry", {}).get("group", {}).keys())


def get_dependency_groups_for_lambdas(poetry_dependency_groups: set[str]) -> list[str]:
    """
    Return a list of poetry dependency groups for lambdas.
    Note that the poetry dependency group name and the lambda names are the same
    """
    lambda_dirs = [d for d in LAMBDA_BASE_DIR.iterdir() if d.is_dir()]

    lambda_dependency_groups = []
    for lambda_dir in lambda_dirs:
        lambda_name = lambda_dir.name
        if lambda_name in poetry_dependency_groups:
            lambda_dependency_groups.append(lambda_name)

    return lambda_dependency_groups


def get_boilerplate_layer_dependency_group(poetry_dependency_groups: set[str]) -> str:
    """
    Validate that boilerplate dependency group exists and return layer name
    Note that the poetry dependency group name and the layer name are the same
    """
    layer_name = BOILERPLATE_LAYER_DIR.name
    if layer_name not in poetry_dependency_groups:
        raise ValueError(
            "Boilerplate Layer dependency group not found in pyproject.toml"
        )

    return layer_name


def export_requirements_for_lambdas(poetry_dependency_groups: set[str]):
    """
    Export requirements.txt for lambdas
    """
    lambda_dependency_groups = get_dependency_groups_for_lambdas(
        poetry_dependency_groups
    )
    for lambda_name in lambda_dependency_groups:
        lambda_path = LAMBDA_BASE_DIR / lambda_name
        export_requirements(lambda_name, lambda_path)


def export_requirements_for_layer(poetry_dependency_groups: set[str]):
    """
    Export requirements.txt for boilerplate layer
    """
    layer_name = get_boilerplate_layer_dependency_group(poetry_dependency_groups)
    layer_path = BOILERPLATE_LAYER_DIR
    export_requirements(layer_name, layer_path)


def export_requirements(dependency_group: str, out_path: Path):
    """
    Export requirements.txt for the given dependency group and out_path
    """
    print(f"Generating requirements.txt for {dependency_group} in {out_path})...")
    requirements_out_file = out_path / "requirements.txt"
    cmd = f"poetry export -f requirements.txt --without-hashes --without dev --with {dependency_group} -o {requirements_out_file}"
    subprocess.run(cmd, shell=True, check=True)


def main():
    """
    Run poetry export to create requirements.txt files for lambda applications and layers.
    """
    all_poetry_dependency_groups = get_dependency_groups()
    export_requirements_for_lambdas(all_poetry_dependency_groups)
    export_requirements_for_layer(all_poetry_dependency_groups)
    print("Finished generating requirements.txt files")


if __name__ == "__main__":
    main()
