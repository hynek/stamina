# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import pathlib
import shutil
import tomllib

import nox
import nox_uv


nox.options.sessions = [
    "ruff",
    "pre_commit",
    "tests",
    "typing_api",
    "mypy_api",
    "mypy_pkg",
]

# We don't need this for packaging, but Mypy is extremely slow on its first
# run.
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True

nox.needs_version = ">=2026.08.10"
nox.options.default_venv_backend = "uv"


pyp = tomllib.loads(pathlib.Path("pyproject.toml").read_text())
ALL_SUPPORTED = [
    pv.rsplit(" ")[-1]
    for pv in pyp["project"]["classifiers"]
    if pv.startswith("Programming Language :: Python :: ")
]


def _install_pkg(
    session: nox.Session, pkg: str = ".", *, editable: bool = False
) -> None:
    """
    Install *pkg* on top of the locked dependencies installed by nox-uv.

    Always reinstall it, so reused virtualenvs never test a stale build.
    """
    session.install(
        "--no-deps",
        "--reinstall-package=stamina",
        *(["-e"] if editable else []),
        pkg,
    )


@nox_uv.session(tags=["lint"], allow_parallel=True, uv_only_groups=["lint"])
def ruff(session: nox.Session) -> None:
    session.run("ruff", "check", "--fix", "--exit-non-zero-on-fix", ".")
    session.run("ruff", "format", "--exit-non-zero-on-format", ".")


@nox_uv.session(tags=["lint"], allow_parallel=True, uv_only_groups=["lint"])
def pre_commit(session: nox.Session) -> None:
    session.run("prek", "run", "--all-files")


@nox_uv.session(
    python=ALL_SUPPORTED,
    tags=["typing"],
    allow_parallel=True,
    uv_groups=["mypy"],
    uv_no_install_project=True,
)
def mypy_api(session: nox.Session) -> None:
    _install_pkg(session)

    session.run("mypy", "typing_tests")


@nox_uv.session(
    tags=["typing"],
    allow_parallel=True,
    uv_groups=["mypy"],
    uv_no_install_project=True,
)
def mypy_pkg(session: nox.Session) -> None:
    _install_pkg(session)

    session.run("mypy", "src", "typing_tests", "noxfile.py")


@nox_uv.session(
    python=ALL_SUPPORTED[-1],
    tags=["typing"],
    allow_parallel=True,
    # nox-uv's groups can't depend on parameters, so install all tools.
    uv_groups=["pyright", "pyrefly", "ty"],
    uv_no_install_project=True,
)
@nox.parametrize("tool", ["pyright", "pyrefly", "ty"])
def typing_api(session: nox.Session, tool: str) -> None:
    """
    Check type hints using Python version-independent tools.
    """
    _install_pkg(session)

    cmd_line = {
        "pyright": ("pyright",),
        "pyrefly": ("pyrefly", "check"),
        "ty": ("ty", "check"),
    }

    session.run(*cmd_line[tool], "typing_tests")


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

    return pkg, posargs


@nox.session(python=ALL_SUPPORTED, allow_parallel=True)
@nox.parametrize(
    "opt_group",
    [None, "instrumentation", "trio"],
    ids=["minimal", "instrumentation", "trio"],
)
def tests(session: nox.Session, opt_group: str | None) -> None:
    pkg, posargs = _get_pkg(session.posargs)

    # nox-uv's groups can't depend on parameters, so we have to sync by hand.
    # Don't sync on top of nox-uv: uv may recreate the venv on each sync.
    session.run_install(
        "uv", "sync", "--locked", "--no-default-groups", "--no-install-project",
        "--group=cov", *([f"--group={opt_group}"] if opt_group else []),
    )  # fmt: skip
    _install_pkg(session, pkg)

    session.run("coverage", "run", "-m", "pytest", *posargs)


@nox_uv.session(requires=ALL_SUPPORTED, uv_only_groups=["cov"])
def coverage_report(session: nox.Session) -> None:
    session.run("coverage", "combine")
    session.run("coverage", "report")


@nox_uv.session(uv_groups=["docs"], uv_no_install_project=True)
def docs(session: nox.Session) -> None:
    shutil.rmtree("docs/_build", ignore_errors=True)

    if session.posargs and session.posargs[0] == "watch":
        _install_pkg(session, editable=True)
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
            "-n "
            "docs "
            "docs/_build/html",
        )
        return

    _install_pkg(session)
    cmds = session.posargs or ["html", "doctest"]

    dest = os.environ.get("READTHEDOCS_OUTPUT", "docs/_build/")

    for cmd in cmds:
        session.run(
            "python", "-Im", "sphinx",
            "-T", "-E",
            "-W", "--keep-going",
            "-b", cmd,
            "-d", "docs/_build/doctrees",
            "-D", "language=en",
            "-n",
            "docs",
            pathlib.Path(dest, "html")
        )  # fmt: skip
