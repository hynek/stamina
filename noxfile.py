# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os

import nox


nox.options.sessions = ["pre_commit", "tests", "tests_no_deps", "mypy"]
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True

ALL_SUPPORTED = ["3.8", "3.9", "3.10", "3.11", "3.12"]


@nox.session
def pre_commit(session: nox.Session) -> None:
    session.install("pre-commit")

    session.run("pre-commit", "run", "--all-files")


@nox.session(python=ALL_SUPPORTED)
def mypy(session: nox.Session) -> None:
    session.install(".[typing]", "structlog", "prometheus-client")

    session.run("mypy", "src", "typing_examples.py")


@nox.session(python=ALL_SUPPORTED)
def tests(session: nox.Session) -> None:
    session.install(
        ".[tests]", "coverage[toml]", "structlog", "prometheus-client"
    )

    session.run("coverage", "run", "-m", "pytest", *session.posargs)

    if os.environ.get("CI") != "true":
        session.notify("coverage_report")


@nox.session
def tests_no_deps(session: nox.Session) -> None:
    session.install(".[tests]", "coverage[toml]")

    session.run("coverage", "run", "-m", "pytest", *session.posargs)

    if os.environ.get("CI") != "true":
        session.notify("coverage_report")


@nox.session
def coverage_report(session: nox.Session) -> None:
    session.install("coverage[toml]")

    session.run("coverage", "combine")
    session.run("coverage", "report")
