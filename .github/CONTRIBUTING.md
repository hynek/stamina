# How To Contribute

First off, thank you for considering contributing!
It's people like *you* who make it is such a great tool for everyone.

This document is mainly to help you to get started by codifying tribal knowledge and expectations and make it more accessible to everyone.
But don't be afraid to open half-finished PRs and ask questions if something is unclear!


## Workflow

- No contribution is too small!
  Please submit as many fixes for typos and grammar bloopers as you can!
- Try to limit each pull request to *one* change only.
- Since we squash on merge, it's up to you how you handle updates to the main branch.
  Whether you prefer to rebase on main or merge `main` into your branch, do whatever is more comfortable for you.
- *Always* add tests and docs for your code.
  This is a hard rule; patches with missing tests or documentation won't be merged.
- Consider updating [CHANGELOG.md][changelog] to reflect the changes as observed by people using this library.
- Make sure your changes pass our [CI].
  You won't get any feedback until it's green unless you ask for it.
- Don’t break [backwards-compatibility].


## Local Development Environment

You can (and should) run our test suite using [Nox].
However, you’ll probably want a more traditional environment as well.

We recommend using the Python version from the `.python-version-default` file in the project's root directory, because that's the one that is used in the CI by default, too.

If you're using [*direnv*](https://direnv.net), you can automate the creation of the project virtual environment with the correct Python version by adding the following `.envrc` to the project root:

```bash
layout python python$(cat .python-version-default)
```

You can now install the package with its development dependencies into the virtual environment:

```console
$ pip install -e .[dev]
```

This will also install [Nox] for you.

Now you can run the test suite:

```console
$ python -m pytest
```

For documentation, you can use:

```console
$ nox --session docs -- watch
```

This will build the documentation, and then watch for changes and rebuild it whenever you save a file.

To just build the documentation and run doctests, use:

```console
$ nox --session docs
```

You will find the built documentation in `docs/_build/html`.


## Code

- Obey [PEP 8] and [PEP 257].
  We use the `"""`-on-separate-lines style for docstrings with [Napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)-style API documentation:

  ```python
  def func(x: str) -> str:
      """
      Do something.

      Parameters:
        x: A very important parameter.

      Returns:
        The result of doing something.
      """
  ```

  Please note that unlike everything else, the API docstrings are still [reStructuredText].

- If you add or change public APIs, tag the docstring using `..  versionadded:: 23.1.0 WHAT` or `..  versionchanged:: 23.1.0 WHAT`.
  We follow CalVer, so the next version will be the current with with the middle number incremented (e.g. `23.1.0` -> `23.2.0`).

- We use [Ruff] to sort our imports, and we follow the [Black] code style with a line length of 79 characters.
  As long as you run our full [Nox] suite before committing, or install our [*pre-commit*] hooks, you won't have to spend any time on formatting your code at all.
  If you don't, CI will catch it for you -- but that seems like a waste of your time!


## Tests

- Write your asserts as `expected == actual` to line them up nicely and leave an empty line before them:

  ```python
  x = f()

  assert 42 == x.some_attribute
  assert "foo" == x._a_private_attribute
  ```

- To run the test suite, all you need is a recent [Nox].
  It will ensure the test suite runs with all dependencies against all Python versions just as it will in our CI.

- Write [good test docstrings].


## Documentation

- Use [semantic newlines] in Markdown files (files ending in `.md`):

  ```markdown
  This is a sentence.
  This is another sentence.
  ```

- If you start a new section, add two blank lines before and one blank line after the header except if two headers follow immediately after each other:

  ```markdown
  Last line of previous section.


  ## Header of New Top Section

  ### Header of New Section

  First line of new section.
  ```

- If your change is noteworthy, add an entry to the [changelog].
  Use [semantic newlines], and add a link to your pull request:

  ```markdown
  - Added `stamina.func()` that does foo.
    It's pretty cool.
    [#1](https://github.com/hynek/stamina/pull/1)
  - `stamina.func()` now doesn't crash the Large Hadron Collider anymore.
    That was a nasty bug!
    [#2](https://github.com/hynek/stamina/pull/2)
  ```

---

Again, this list is mainly to help you to get started by codifying tribal knowledge and expectations.
If something is unclear, feel free to ask for help!

Please note that this project is released with a Contributor [Code of Conduct].
By participating in this project you agree to abide by its terms.
Please report any harm to [Hynek Schlawack] in any way you find appropriate.



[ci]: https://github.com/hynek/stamina/actions
[backwards-compatibility]: https://github.com/hynek/stamina/blob/main/.github/SECURITY.md
[changelog]: https://github.com/hynek/stamina/blob/main/CHANGELOG.md
[nox]: https://nox.thea.codes/
[semantic newlines]: https://rhodesmill.org/brandon/2012/one-sentence-per-line/
[Ruff]: https://github.com/astral-sh/ruff
[*pre-commit*]: https://pre-commit.com/
[Black]: https://github.com/psf/black
[reStructuredText]: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
[good test docstrings]: https://jml.io/test-docstrings/
[code of conduct]: https://github.com/hynek/stamina/blob/main/.github/CODE_OF_CONDUCT.md
[Hynek Schlawack]: https://hynek.me/about/
[pep 257]: https://peps.python.org/pep-0257/
[pep 8]: https://peps.python.org/pep-0008/
