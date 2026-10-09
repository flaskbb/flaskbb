# Contributing

We love contributions from everyone.


## Support Questions

Don't use the GitHub's Issue tracker for general Python and Flask related
questions. For FlaskBB it is ok _for now_. ``#python`` and
[Stack Overflow][stackoverflow] is also worth considering for asking
support questions.

  [stackoverflow]: https://stackoverflow.com/

You can also join the [FlaskBB Matrix chat][matrix] to ask questions or
discuss development.

  [matrix]: https://matrix.to/#/#flaskbb:matrix.org


## Reporting Issues

Please provide as many details as possible. This will make it easier for
us to figure out what went wrong.


## Contributing Code

FlaskBB uses [uv][uv] to manage dependencies and run everything below. Once
uv is installed, `uv sync` in the project root sets up a working dev
environment - no separate requirements file to install from.

  [uv]: https://docs.astral.sh/uv/

Format and lint your code with [ruff][ruff] before submitting:

    make format

  [ruff]: https://docs.astral.sh/ruff/

Then run the testsuite:

    make test

Both `make` targets are thin wrappers around `uv run ruff ...` / `uv run
pytest`; run those directly if you'd rather not use `make`.


Mention how your changes affect the project to other developers and users in the
`NEWS.md` file.

If your change adds or edits a translatable string, see
[Localization](https://flaskbb.readthedocs.io/en/latest/development/localization) for what to do about it.


## Translating FlaskBB

FlaskBB is translated via [Weblate](https://hosted.weblate.org/projects/flaskbb/flaskbb/).
See [Localization](https://flaskbb.readthedocs.io/en/latest/development/localization) for how to get started as a translator.

Push to your fork. Write a [good commit message][commit]. Submit a pull request.

  [commit]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html

Others will give constructive feedback.
This is a time for discussion and improvements, and making the necessary
changes will be required before we can merge the contribution.
