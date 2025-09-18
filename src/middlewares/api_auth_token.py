from src.app import app
from flask import request, make_response
import logging
import jwt
import json

from src.handler.error_handler import UnauthorizedError, UnexpectedError

log = logging.getLogger(__name__)


class requires:
  def __init__(self, permissions):
    self.permissions = permissions

  def __call__(self, func):
    def wrapper(*args, **kwargs):
      token = None
      if 'x-access-token' in request.headers:
        token = request.headers['x-access-token']
        if token == app.config['TOKEN']:
          return initialize_response(self, func, True, token, *args, **kwargs)
      raise UnauthorizedError()


def check_request_token(permissions ,token):
  decoded_token = decode_token(token)
  print(decoded_token)
  print(decoded_token['userId'], '===')
  try:
    user = User.query.filter_by(id = decoded_token['userId'], publicId = decoded_token['publicId']).first()
    if user:
      token = user.encodeToken()
      return user, token
    else:
      raise UnauthorizedError("User does not exist")
  except Exception as e:
    raise UnauthorizedError()

def decode_token(token):
  if not token:
    raise UnauthorizedError('token is missing')
  try:
    decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms="HS256")
  except jwt.ExpiredSignatureError:
    raise UnauthorizedError("your token has been expired")
  except Exception:
    raise UnexpectedError("Error decoding token {}".format(token))
  return decoded_token

def initialize_response(self, func, has_token, new_token, *args, **kwargs):
  code = 200
  ret = func(*args, **kwargs)
  if isinstance(ret, tuple):
    code = ret[1]
    ret = ret[0]
  try:
    response = make_response(json.dumps(ret), code)
    if has_token:
      response.headers.extend({'x-access-token': new_token})
  except Exception as e:
    response = ret
  log.debug("Response: {}".format(response))
  return response