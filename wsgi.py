from flaskbb import create_app
from flaskbb.configs.example import ProductionConfig

flaskbb = create_app(config=ProductionConfig())
