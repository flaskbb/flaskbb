import os
from flaskbb import create_app

_basepath = os.path.dirname(os.path.abspath(__file__))

# will throw an error if the config doesn't exist
flaskbb = create_app(config=os.path.join(_basepath, 'flaskbb.cfg'))
