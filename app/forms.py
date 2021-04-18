from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, HiddenField
from wtforms.validators import ValidationError, DataRequired, EqualTo, \
    Length
from flask_wtf.file import FileField, FileAllowed
from app.models import User


class LoginForm(FlaskForm):
    id = StringField('ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    id = StringField('ID', validators=[DataRequired()])
    user_name = StringField('User name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirmPassword = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_user_name(self, user_name):
        user = User().get_obj('user_name', user_name.data)
        if user is not None:
            raise ValidationError('The Username already exists')

    def validate_id(self, id):
        user = User().get_obj('id', id.data)
        if user is not None:
            raise ValidationError('The ID already exists')


class EditProfileForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    newPassword = PasswordField(
        'New Password', validators=[DataRequired()])
    confirmPassword = PasswordField(
        'Repeat New Password', validators=[DataRequired(), EqualTo('newPassword')])
    submit = SubmitField('Change password')


class PostForm(FlaskForm):
    subject = TextAreaField('Subject name', validators=[DataRequired()])
    text = TextAreaField('Subject text', validators=[DataRequired()])
    submit = SubmitField('Submit')
