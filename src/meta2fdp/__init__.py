"""meta2fdp package entry point.

This module exposes a lightweight CLI entry point for the package script defined in
`pyproject.toml`. The package is primarily intended for library usage via the
pipeline APIs, but the console script can also confirm the install and point
users to the documentation.
"""

__version__ = "0.1.0"


def main() -> int:
    """Console entry point for the meta2fdp package."""
    print("meta2fdp is installed.")
    print(
        "Use the Python API or see the documentation in docs/source for usage examples."
    )
    return 0
