from flask_restful import Resource
from src.handler.error_handler import InvalidDataError
from flask import request
import json, re, requests

from .use_case import get_properties

# middleare
from src.middlewares.api_auth_token import requires


class Properties(Resource):
  method_decorators = [requires()]

  def post(self):
      """Accept arbitrary text, JSON, or form data and pass it as a string.

      - If JSON (any structure), stringify the entire payload.
      - If form data, use the single field's value; if multiple fields, stringify the dict.
      - If raw text (text/plain), use the body as-is.
      """
      prompt = None

      if request.is_json:
          data = request.get_json(silent=True)
          try:
              prompt = json.dumps(data, ensure_ascii=False)
          except Exception:
              prompt = str(data)
      else:
          form_dict = request.form.to_dict(flat=True)
          if form_dict:
              if len(form_dict) == 1:
                  prompt = next(iter(form_dict.values()))
              else:
                  prompt = json.dumps(form_dict, ensure_ascii=False)
          elif request.data:
              try:
                  prompt = request.get_data(as_text=True)
              except Exception:
                  prompt = None

      if not isinstance(prompt, str) or not prompt.strip():
          raise InvalidDataError("Request body must provide non-empty input as text, JSON, or form data.")

      return get_properties(prompt.strip())
