# Contributing

We love contributions from everyone.


## Support Questions

Don't use the GitHub's Issue tracker for general Python and Flask related
questions. For FlaskBB it is ok _for now_. ``#python`` and
[Stack Overflow][stackoverflow] is also worth considering for asking
support questions.

  [stackoverflow]: https://stackoverflow.com/


## Reporting Issues

Please provide as many details as possible. This will make it easier for
us to figure out what went wrong.


## Contributing Code

Follow the [PEP8 style guide][pep8].

  [pep8]: https://www.python.org/dev/peps/pep-0008/

You can check if your code follows the PEP8, either by running ``make lint``
or by executing ``flake8`` directly.

FlaskBB is depending on a few python packages for development. One of those is
[py.test][pytest] which runs our testsuite. Just use the provided
``requirements-dev.txt`` file and you should be good to go.

    pip install -r requirements-dev.txt

Then you can run the testsuite with:

    py.test

alternatively you can also use ``make``

    make test


Mention how your changes affect the project to other developers and users in the
`NEWS.md` file.

Push to your fork. Write a [good commit message][commit]. Submit a pull request.

  [commit]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html

Others will give constructive feedback.
This is a time for discussion and improvements, and making the necessary
changes will be required before we can merge the contribution.
