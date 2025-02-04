"""
Pydantic Validators
"""

import re


def convert_runtime(runtime: str) -> str:
    """
    Ensure that minutes and hours don't overflow
    """
    if runtime:
        if "PT" in runtime:
            # Runtime is in ISO 8601 duration format
            match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", runtime)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)

                # Convert minutes to hours if necessary
                total_minutes = hours * 60 + minutes
                hours, minutes = divmod(total_minutes, 60)

                # Format the runtime as ISO 8601 duration
                runtime = f"PT{hours}H{minutes}M{seconds}S"
            else:
                raise ValueError(f"Invalid RunTime format: {runtime}")
        else:
            raise ValueError(f"Invalid RunTime format: {runtime}")

    return runtime
