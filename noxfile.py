# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import pathlib
import shutil
import sys

import nox


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


nox.options.sessions = ["pre_commit", "tests", "mypy_api", "mypy_pkg"]
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
def mypy_api(session: nox.Session) -> None:
    session.install(".[typing]", "structlog", "prometheus-client")

    session.run("mypy", "tests/typing")


@nox.session
def mypy_pkg(session: nox.Session) -> None:
    session.install(".[typing]", "structlog", "prometheus-client")

    session.run("mypy", "src", "tests/typing", "noxfile.py")


def _get_pkg(posargs: list[str]) -> tuple[str, list[str]]:
    """
    Allow `--installpkg path/to/wheel.whl` to be passed.
    """
    posargs = list(posargs)

    try:
        i = posargs.index("--installpkg")
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


@nox.session
def docs(session: nox.Session) -> None:
    shutil.rmtree("docs/_build", ignore_errors=True)

    if session.posargs and session.posargs[0] == "watch":
        session.install("-e", ".[docs]", "watchfiles")
        session.run(
            "watchfiles",
            "--ignore-paths",
            "docs/_build",
            "python -Im sphinx "
            "-T -E "
            "-W --keep-going "
            "-b html "
            "-d docs/_build/doctrees "
            "-D language=en "
            "docs "
            "docs/_build/html",
        )
        return

    session.install(".[docs]")
    cmds = session.posargs or ["html", "doctest"]

    for cmd in cmds:
        session.run(
            # fmt: off
            "python", "-Im", "sphinx",
            "-T", "-E",
            "-W", "--keep-going",
            "-b", cmd,
            "-d", "docs/_build/doctrees",
            "-D", "language=en",
            "docs",
            "docs/_build/html",
            # fmt: on
        )
