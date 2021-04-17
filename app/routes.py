import os
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, session, after_this_request, send_file
from flask_login import login_user, logout_user, current_user, login_required
from google.cloud import storage
from google.cloud.datastore import Client, Key
from resizeimage import resizeimage
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

import config
from app import app
from app.forms import LoginForm, RegistrationForm, PostForm, EditProfileForm
from app.models import User, Post


def getusername(id):
    user = User().get_obj('id', id)
    return user.id


def deletebucketimg(imgname):
    gcs = storage.Client()
    bucket = gcs.get_bucket(config.Config.CLOUD_STORAGE_BUCKET)
    blob = bucket.blob(imgname)
    blob.delete()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User()
            user.id = form.id.data
            user.user_name = form.user_name.data
            user.set_password(form.password.data)
            user.set_avatar()
            user.save()
            flash('Congratulations, successfully registered!')
            return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User().get_obj('id', form.id.data)
        if user is None:
            flash('Invalid ID or password')
            return redirect(url_for('login'))
        elif not user.check_password(form.password.data):
            flash('Invalid ID or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    client = Client()
    query = client.query(kind="post")
    query.order = ["-date_created"]
    posts = []
    for task in query.fetch(10):
        posts.append(
            {'img_name': task["img_name"],
             'subject': task["subject"],
             'text': task["text"],
             'date_created': task["date_created"],
             'keyid': int(task.key.id),
             'user_id': task["user_id"],
             'user_name': getusername(task["user_id"])})
    if posts:
        return render_template('index.html', title='Home', form=form, posts=posts)
    return render_template('index.html', title='Home', form=form)


@app.route('/editpost/<postkey>', methods=['GET'])
def editpost(postkey):
    form = PostForm()
    client = Client()
    post = client.get(Key('post', int(postkey), project=config.Config.GOOGLE_PROJECT))
    if post['user_id'] != current_user.id:
        flash('Can not edit other user''s post')
        return redirect(url_for('index'))
    form.subject.data = post['subject']
    form.text.data = post['text']
    session['update_post_id'] = postkey

    return render_template('editpost.html', title='Home', form=form)


@app.route('/editpost', methods=['POST'])
def updatepost():
    client = Client()
    form = PostForm()
    post = client.get(Key('post', int(session.get('update_post_id', None)), project=config.Config.GOOGLE_PROJECT))
    """Process the update file and upload it to Google Cloud Storage."""
    uploaded_file = request.files.get('file')
    if uploaded_file:
        imgname = secure_filename(uploaded_file.filename)
        imgname = current_user.id + '_' + imgname
        # Create a Cloud Storage client.
        gcs = storage.Client()

        # Get the bucket that the file will be uploaded to.
        bucket = gcs.get_bucket(config.Config.CLOUD_STORAGE_BUCKET)

        # Create a new blob and upload the file's content.
        blob = bucket.blob(imgname.lower())

        blob.upload_from_string(
            uploaded_file.read(),
            content_type=uploaded_file.content_type
        )
        deletebucketimg(post['img_name'])
        post['img_name'] = imgname.lower()
    post['subject'] = form.subject.data
    post['text'] = form.text.data
    client.put(post)
    return redirect(url_for('index'))


@app.route('/upload', methods=['POST'])
def upload():
    """Process the uploaded file and upload it to Google Cloud Storage."""
    uploaded_file = request.files.get('file')
    form = PostForm()
    if not uploaded_file:
        return 'No file uploaded.', 400

    imgname = secure_filename(uploaded_file.filename)
    imgname = current_user.id + '_' + imgname
    # Create a Cloud Storage client.
    gcs = storage.Client()

    # Get the bucket that the file will be uploaded to.
    bucket = gcs.get_bucket(config.Config.CLOUD_STORAGE_BUCKET)

    # Create a new blob and upload the file's content.
    blob = bucket.blob(imgname.lower())

    blob.upload_from_string(
        uploaded_file.read(),
        content_type=uploaded_file.content_type
    )
    post = Post()
    post.subject = form.subject.data
    post.text = form.text.data
    post.img_name = imgname.lower()
    post.user_id = current_user.id
    post.save()
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/getimg/<object>')
def getimg(object):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(config.Config.CLOUD_STORAGE_BUCKET)
    blob = bucket.blob(object)
    tmpdirname = config.basedir + '/tmpdata'
    fullpath = os.path.join(tmpdirname, object)
    blob.download_to_filename(fullpath)
    with open(fullpath, 'r+b') as f:
        with Image.open(f) as image:
            cover = resizeimage.resize_cover(image, [128, 128])
            cover.save(fullpath, image.format)

    @after_this_request
    def remove_file(response):
        if request.endpoint == "generate_image":
            if os.path.isfile(fullpath):
                os.remove(fullpath, mimetype='image/gif')
        return response

    return send_file(fullpath)


@app.route('/user/<user_name>')
@login_required
def user(user_name):
    user = User().get_obj('user_name', user_name)
    client = Client()
    query = client.query(kind="post")
    query = query.add_filter("user_id", "=", user.id)
    query.order = ["-date_created"]
    posts = []
    for task in query.fetch(10):
        posts.append(
            {'img_name': task["img_name"],
             'subject': task["subject"],
             'text': task["text"],
             'date_created': task["date_created"],
             'keyid': int(task.key.id),
             'user_id': task["user_id"],
             'user_name': user_name})
    if posts:
        return render_template('user.html', user=user, posts=posts)
    return render_template('user.html', user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            flash('Invalid password')
            return redirect(url_for('edit_profile'))
        current_user.set_password(form.newPassword.data)
        current_user.save()
        flash('Changed password')

        return redirect(url_for('logout'))
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)
