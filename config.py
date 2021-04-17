import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '347b03891b8b4c3c89cb938f5d2cecaa'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLOUD_STORAGE_BUCKET = 'flask-forum-bucket'
    GOOGLE_PROJECT = 'flaskforum-311009'
