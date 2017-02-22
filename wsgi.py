from flaskbb import create_app

# will throw an error if the config doesn't exist
flaskbb = create_app(config="flaskbb.cfg")
