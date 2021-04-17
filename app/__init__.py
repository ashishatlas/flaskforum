from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from config import Config, basedir
from flask_moment import Moment

app = Flask(__name__)
app.config.from_object(Config)
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
bootstrap = Bootstrap(app)
moment = Moment(app)
login = LoginManager(app)
login.login_view = 'login'

from app import routes, models
