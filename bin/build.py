#!/usr/bin/env python3

import click
import os
from pathlib import Path

from utils import *

WORKFOLDER = Path(os.path.abspath(__file__)).parent.parent


@click.command()
@click.option("--check/--no-check", default=True)
@click.option("--decompile/--no-decompile", default=True)
@click.option("-v", "--verbose", count=True)
def build(check, decompile, verbose):
    """Rebuild the benchmark-suite."""

    logger = setup_logger(verbose)
    suite = Suite(WORKFOLDER, QUERIES, logger)

    suite.build()
    suite.update_cases()

    if check:
        suite.check()

    if decompile:
        suite.decompile()


if __name__ == "__main__":
    build()
