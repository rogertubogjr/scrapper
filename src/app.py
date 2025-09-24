from flask import Flask, got_request_exception
from flask_restful import Api
from flask_cors import CORS
import logging, sys
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask('rtg', instance_relative_config=True)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
api = Api(app)

if app.config['DEBUG']:
    print("Running in debug mode")
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    CORS(app, expose_headers=['x-access-token'])

log = logging.getLogger(__name__)

def log_exception(sender, exception, **extra):
    sender.logger.exception(exception)

got_request_exception.connect(log_exception, app)

import src.routes.property