import datetime

from datastore_entity import DatastoreEntity, EntityValue
from flask_login import UserMixin
from app import login


class User(DatastoreEntity, UserMixin):
    id = EntityValue(None)
    user_name = EntityValue(None)
    password = EntityValue(None)
    user_img_name = EntityValue(None)
    # specify the name of the entity kind.
    __kind__ = "user"
    __exclude_from_index__ = ['password']

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password

    def set_avatar(self):
        self.user_img_name = self.id[-1] + '.jpg'

    def get_avatar(self):
        return self.user_img_name


@login.user_loader
def load_user(id):
    return User().get_obj('id', id)


class Post(DatastoreEntity):
    subject = EntityValue(None)
    text = EntityValue(None)
    user_id = EntityValue(None)
    date_created = EntityValue(datetime.datetime.utcnow())
    img_name = EntityValue(None)

    __kind__ = "post"

    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)

    def __repr__(self):
        return '<Post {}>'.format(self.text)

    def get_subject(self):
        return self.subject.__getattribute__()
