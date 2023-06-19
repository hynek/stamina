# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import pathlib

import nox


try:
    import tomllib
except ImportError:
    import tomli as tomllib


nox.options.sessions = ["pre_commit", "tests", "mypy"]
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True


pyp = tomllib.loads(pathlib.Path("pyproject.toml").read_text())
ALL_SUPPORTED = [
    pv.rsplit(" ")[-1]
    for pv in pyp["project"]["classifiers"]
    if pv.startswith("Programming Language :: Python :: ")
]


@nox.session
def pre_commit(session: nox.Session) -> None:
    session.install("pre-commit")

    session.run("pre-commit", "run", "--all-files")


@nox.session(python=ALL_SUPPORTED)
def mypy(session: nox.Session) -> None:
    session.install(".[typing]", "structlog", "prometheus-client")

    session.run("mypy", "src", "tests/typing")


def _get_pkg(posargs) -> tuple[str, list]:
    """
    Allow `--use-wheel path/to/wheel.whl` to be passed.
    """
    posargs = list(posargs)

    try:
        i = posargs.index("--use-wheel")
        pkg = posargs[i + 1]
        del posargs[i : i + 2]
    except ValueError:
        pkg = "."

    return pkg + "[tests]", posargs


@nox.session(python=ALL_SUPPORTED)
@nox.parametrize("opt_deps", [[], ["structlog", "prometheus-client"]])
def tests(session: nox.Session, opt_deps: list[str]) -> None:
    pkg, posargs = _get_pkg(session.posargs)

    session.install(pkg, "coverage[toml]", *opt_deps)

    session.run("coverage", "run", "-m", "pytest", *posargs)

    if os.environ.get("CI") != "true":
        session.notify("coverage_report")


@nox.session
def coverage_report(session: nox.Session) -> None:
    session.install("coverage[toml]")

    session.run("coverage", "combine")
    session.run("coverage", "report")
