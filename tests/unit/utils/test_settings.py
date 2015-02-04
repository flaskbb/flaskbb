from flaskbb._compat import iterkeys
from flaskbb.utils.settings import FlaskBBConfig


def test_flaskbb_config(default_settings):
    flaskbb_config = FlaskBBConfig()

    assert len(flaskbb_config) > 0
    # test __getitem__
    assert flaskbb_config['PROJECT_TITLE'] == 'FlaskBB'
    # test __setitem__
    flaskbb_config['PROJECT_TITLE'] = 'FlaskBBTest'
    assert flaskbb_config['PROJECT_TITLE'] == 'FlaskBBTest'
    # test __iter__
    assert iterkeys(flaskbb_config).next() == "USERS_PER_PAGE"
