import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import app
from app.admin.models import User
from app.manage import login_required, db
from app.post.models import Post
from werkzeug.utils import secure_filename
import os

post_blueprint = Blueprint('[post]', __name__)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@post_blueprint.route('/post')
@login_required
def list_post():
    username = session.get('username')
    page = request.args.get('page')
    if page is None:
        page = 1
    else:
        page = int(page)

    total_data = db.session.query(Post).from_self().join(Post.user).filter(User.username == username).count()
    limit = 10
    offset = (page - 1) * limit

    posts = db.session.query(Post).limit(limit).from_self()\
        .join(Post.user).filter(User.username == username)\
        .limit(limit).offset(offset).all()

    has_next = False
    if total_data > (offset + len(posts)):
        has_next = True

    has_prev = False
    if page > 1:
        has_prev = True

    upload_folder = app.app.config['UPLOAD_FOLDER']

    return render_template('post.html', posts=posts, page_title='My Post',
                           has_next=has_next, has_prev=has_prev, page=page, upload_folder=upload_folder)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@post_blueprint.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        is_form_valid = True

        if title.strip() == '':
            is_form_valid = False
            flash('username should be filled!', 'error')
        if content.strip() == '':
            is_form_valid = False
            flash('content should be filled!', 'error')

        # check if the post request has the file part
        if 'image_file' not in request.files:
            flash('No file part', 'error')
            return render_template('create_post.html')

        filename = None
        file = request.files['image_file']

        # if user does not select file, browser also
        # submit an empty part without filename
        # if file.filename == '':
        #     flash('No selected file')
        #     return redirect(request.url)

        if file and not allowed_file(file.filename):
            is_form_valid = False
            flash('file not allowed!', 'error')
        elif file:
            filename = secure_filename(file.filename)
            now = datetime.datetime.now()
            filename = now.strftime("%d%m%Y%H%M%S") + filename
            file.save(os.path.join(app.app.config['UPLOAD_FOLDER'], filename))

        if not is_form_valid:
            return render_template('create_post.html')

        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('user not found!', 'error')
            return render_template('create_post.html')

        post = Post()
        post.user = user
        post.title = title
        post.content = content
        post.image_path = filename
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('[post].list_post'))
    else:
        return render_template('create_post.html')


@post_blueprint.route('/edit-post', methods=['GET', 'POST'])
@login_required
def edit_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        post_id = request.form['post_id']
        is_form_valid = True

        post = db.session.query(Post).get(post_id)

        if post is None:
            flash('post not found!', 'error')
            return render_template('edit_post.html')

        if title.strip() == '':
            is_form_valid = False
            flash('username should be filled!', 'error')
        if content.strip() == '':
            is_form_valid = False
            flash('content should be filled!', 'error')

        if not is_form_valid:
            return render_template('edit_post.html', post=post)

        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('user not found!', 'error')
            return render_template('edit_post.html', post=post)

        if not (post.user_id == user.id):
            flash('user not allowed to edit this post!', 'error')
            return render_template('edit_post.html', post=post)

        post.title = title
        post.content = content

        file = request.files['image_file']

        if file and not allowed_file(file.filename):
            flash('file not allowed!', 'error')
            return render_template('edit_post.html', post=post)
        elif file:
            filename = secure_filename(file.filename)
            now = datetime.datetime.now()
            filename = now.strftime("%d%m%Y%H%M%S") + filename
            file.save(os.path.join(app.app.config['UPLOAD_FOLDER'], filename))
            post.image_path = filename

        # db.session.add(post)
        db.session.commit()
        return redirect(url_for('[post].list_post'))
    else:
        post_id = request.args.get('post_id')
        post = db.session.query(Post).get(post_id)
        return render_template('edit_post.html', post=post)


@post_blueprint.route('/delete-post')
@login_required
def delete_post():
    post_id = request.args.get('post_id')

    try:
        post = db.session.query(Post).get(post_id)

        if post is None:
            flash('post not found!', 'error')
            return render_template('error_page.html')

        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('user not found!', 'error')
            return render_template('error_page.html')

        if not (post.user_id == user.id or user.role == 'admin'):
            flash('user not allowed to delete this post!', 'error')
            return render_template('error_page.html')

        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('[post].list_post'))
    except Exception as e:
        flash(f'Delete post failed {e}', 'error')
        return render_template('error_page.html')
