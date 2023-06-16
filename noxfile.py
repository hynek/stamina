# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os

import nox


nox.options.sessions = ["cog", "pre_commit", "tests", "mypy"]
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True


ALL_SUPPORTED = [
    # [[[cog
    # import tomllib, pathlib
    # sup = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["tool"]["supported-pythons"]
    # for v in sup["all"]:
    #     cog.outl(f'"{v}",')
    # ]]]
    "3.8",
    "3.9",
    "3.10",
    "3.11",
    "3.12",
    # [[[end]]]
]


@nox.session
def cog(session: nox.Session) -> None:
    session.install("cogapp")

    session.run(
        # fmt: off
        "cog", *session.posargs, "-r",
        "pyproject.toml", "noxfile.py", ".github/workflows/ci.yml",
        # fmt: on
    )


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
