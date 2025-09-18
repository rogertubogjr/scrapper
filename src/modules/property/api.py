from flask_restful import Resource
from src.handler.error_handler import InvalidDataError
from flask import request

from .use_case import get_properties

# middleare
from src.middlewares.api_auth_token import requires


class Properties(Resource):
    # @requires([UserType.ADMIN.value])
    def get(self):
        return get_properties()