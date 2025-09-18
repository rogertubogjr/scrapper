from src.app import app
from flask import request, make_response, g
import logging
import jwt
import json, pytz
from datetime import datetime

from src.handler.error_handler import UnauthorizedError, UnexpectedError
from src.db.models.user import User

log = logging.getLogger(__name__)


class requires:
	def __init__(self, permissions):
		self.permissions = permissions

	def __call__(self, func):
		def wrapper(*args, **kwargs):
			token = None
			if 'x-access-token' in request.headers:
				token = request.headers['x-access-token']
				url = str(request.url)

			user, new_token = check_request_token(self.permissions, token)
			g.current_user = user
			if not user and not new_token:
				return initialize_response(self, func, False, new_token, *args, **kwargs)
			g.token = new_token
			user_permission = user.userType.name
			print(user_permission, "================", self.permissions)
			if not user_permission in self.permissions:
				raise UnauthorizedError()

			log.debug("{url} requires {self.permissions} user permission => {user.userType.name}   log_time: {log_time}".format(url = url, self = self, user = user, log_time = datetime.strftime(datetime.now(pytz.timezone('Asia/Manila')), '%B %d,%Y %I:%M %p') ))

			return initialize_response(self, func, True, new_token, *args, **kwargs)
		return wrapper


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