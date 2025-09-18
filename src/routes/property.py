from src.app import api

from src.modules.property.api import Properties

api.add_resource(Properties, '/properties')