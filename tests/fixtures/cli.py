import pytest
from flaskbb.extensions import db


@pytest.fixture
def cli_runner(application):
    """A runner for FlaskBB's click commands.

    Commands run in their own app context and therefore in their own
    session, so the test's data has to be committed before invoking one and
    the test's objects have to be expired afterwards - the runner does both.
    """
    runner = application.test_cli_runner()
    invoke = runner.invoke

    def invoke_and_sync(*args, **kwargs):
        db.session.commit()
        result = invoke(*args, **kwargs)
        db.session.expire_all()
        return result

    runner.invoke = invoke_and_sync
    return runner
