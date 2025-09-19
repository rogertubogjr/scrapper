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

    def post(self):
        """Accept a plain text prompt from clients.

        Accepts either JSON (application/json) with a "prompt" field, or
        form-encoded (application/x-www-form-urlencoded or multipart/form-data)
        with a "prompt" field from a textarea.
        """
        prompt = None

        if request.is_json:
            data = request.get_json(silent=True) or {}
            prompt = data.get("prompt")
        else:
            prompt = request.form.get("prompt")

        if not isinstance(prompt, str) or not prompt.strip():
            raise InvalidDataError("Field 'prompt' is required and must be a non-empty string.")

        prompt = prompt.strip()

        return get_properties(prompt)