"""
CLI to add cProfile profiling
"""

import contextlib
import cProfile
import importlib
import pstats
from functools import wraps
from typing import Any, Callable, TypeVar

import typer
from structlog.stdlib import get_logger

app = typer.Typer(help="Run profiling for CLI commands.", invoke_without_command=False)

log = get_logger()
T = TypeVar("T")
CommandCallback = Callable[..., Any]


@contextlib.contextmanager
def profiler(enable: bool = False, filename: str = "profile.prof"):
    """
    Profiler context manager to profile commands.
    """
    profiler_instance = cProfile.Profile()
    if enable:
        profiler_instance.enable()
    try:
        yield
    finally:
        if enable:
            profiler_instance.disable()
            stats = pstats.Stats(profiler_instance)
            stats.sort_stats(pstats.SortKey.TIME)
            stats.dump_stats(filename)
            print(f"\nProfile data saved to {filename}")
            stats.print_stats(10)


def wrap_with_profiler(command_callback: CommandCallback) -> CommandCallback:
    """
    Wrap a command callback to add profiling logic
    """

    @wraps(command_callback)
    def wrapped(*args: Any, **kwargs: Any):
        with profiler(enable=True, filename="profile.prof"):
            command_callback(*args, **kwargs)

    return wrapped


def register_commands_from_module(module_name: str):
    """
    Dynamically register commands from a given Typer app module.
    """
    module = importlib.import_module(module_name)
    if hasattr(module, "app") and isinstance(module.app, typer.Typer):
        for command in module.app.registered_commands:
            # Wrap the command's callback in profiling logic
            if command.callback is None:
                log.warning(
                    "Command has no callback, skipping.", command_name=command.name
                )
                continue
            wrapped_callback = wrap_with_profiler(command.callback)
            app.command(name=command.name, help=command.help)(wrapped_callback)
    else:
        log.error("Module does not have a valid Typer app.", module_name=module_name)
        raise typer.Exit(1)


# List of all CLI command modules to add profiling to
cli_modules = [
    "tools.initialize_pipeline.cli",
    "tools.file_validation.cli",
    "tools.schema_check.cli",
    "tools.post_schema_check.cli",
    "tools.file_attributes.cli",
    "tools.pti_validation.cli",
    "tools.local_etl.cli",
]

for cli_module in cli_modules:
    register_commands_from_module(cli_module)


if __name__ == "__main__":
    app()
