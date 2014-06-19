from flaskbb import create_app
from flaskbb.configs.production import ProductionConfig

flaskbb = create_app(config=ProductionConfig())
