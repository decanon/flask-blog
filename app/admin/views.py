from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from sqlalchemy import or_

from app.admin.models import User
from app.post.models import Post
from app.manage import db, login_required, admin_required
import app

admin_blueprint = Blueprint('admin', __name__)


@admin_blueprint.route('/')
def home():
    page = request.args.get('page')
    search_keyword = request.args.get('search_keyword')
    if page is None:
        page = 1
    else:
        page = int(page)

    limit = 10
    offset = (page - 1) * limit

    if search_keyword is None:
        posts = db.session.query(Post).limit(limit).offset(offset).from_self().join(Post.user).all()
        total_data = db.session.query(Post).count()
    else:
        posts = db.session.query(Post).limit(limit).offset(offset).from_self()\
            .join(Post.user)\
            .filter(or_(Post.title.like(f'%{search_keyword}%'), Post.content.like(f'%{search_keyword}%')))\
            .all()
        total_data = db.session.query(Post)\
            .filter(or_(Post.title.like(f'%{search_keyword}%'), Post.content.like(f'%{search_keyword}%')))\
            .count()

    has_next = False
    if total_data > (offset + len(posts)):
        has_next = True

    has_prev = False
    if page > 1:
        has_prev = True

    upload_folder = app.app.config['UPLOAD_FOLDER']

    return render_template('index.html', posts=posts, page_title='Home', search_keyword=search_keyword,
                           has_prev=has_prev, has_next=has_next, page=page, upload_folder=upload_folder)


@admin_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username, password)

        # get user
        users = User.query.filter_by(username=username).all()
        if len(users) == 0:
            flash('username / password wrong!', 'error')
            return render_template('login.html')

        # check password
        if User.verify_hash(password, users[0].password) == False:
            flash('username / password wrong!', 'error')
            return render_template('login.html')

        # check is active
        if users[0].is_active == False:
            flash('user is not actived yet!', 'error')
            return render_template('login.html')

        # redirect to home
        session['username'] = username
        session['role'] = users[0].role
        return redirect('/')
    else:
        return render_template('login.html')


@admin_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        is_form_valid = True

        if username.strip() == '':
            is_form_valid = False
            flash('username should be filled!', 'error')
        if password.strip() == '':
            is_form_valid = False
            flash('password should be filled!', 'error')
        if email.strip() == '':
            is_form_valid = False
            flash('email should be filled!', 'error')

        if not is_form_valid:
            return render_template('register.html')

        # check username if already register
        # get user
        users = User.query.filter_by(username=username).all()
        if is_form_valid and len(users) > 0:
            flash('username already registered!', 'error')
            print('username already registered')
            return render_template('register.html')

        user = User()
        user.username = username
        user.password = User.generate_hash(password)
        user.email = email
        user.role = 'user'
        user.is_active = False
        db.session.add(user)
        db.session.commit()
        flash('successfully registered, please wait for admin to activate your account!')
    return render_template('register.html')


@admin_blueprint.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_pwd():
    if request.method == 'POST':
        password1 = request.form['password1']
        password2 = request.form['password2']
        username = session.get('username')

        if password1 == '' or password2 == '':
            flash('password must be filled!', 'error')
            return render_template('change_pwd.html')

        # check password
        if password1 != password2:
            flash('password not match!', 'error')
            return render_template('change_pwd.html')

        # get user
        users = User.query.filter_by(username=username).all()
        if len(users) == 0:
            flash('user not found!', 'error')
            return render_template('change_pwd.html')
        try:
            user = users[0]
            user.password = User.generate_hash(password1)
            db.session.commit()
            flash('password changed successfully!')
        except Exception as e:
            flash(f'db error: {e}', 'error')
    return render_template('change_pwd.html')


@admin_blueprint.route('/my-account', methods=['GET', 'POST'])
@login_required
def my_account():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('user not found!', 'error')
    return render_template('my_acc.html', user=user)


@admin_blueprint.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect('/')


@admin_blueprint.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin():
    page = request.args.get('page')
    search_keyword = request.args.get('search_keyword')

    if page is None: page = 1
    else: page = int(page)

    limit = 10
    offset = (page-1) * limit

    if search_keyword is None:
        total_user = db.session.query(User).count()
        users = db.session.query(User).limit(limit).offset(offset).all()
    else:
        total_user = db.session.query(User).filter(User.username.like(f'%{search_keyword}%')).count()
        users = db.session.query(User).filter(User.username.like(f'%{search_keyword}%'))\
            .limit(limit).offset(offset).all()

    has_next = False
    if total_user > (offset+len(users)):
        has_next = True

    has_prev = False
    if page > 1:
        has_prev = True

    return render_template('list_user.html', users=users, search_keyword=search_keyword,
                           has_next=has_next, has_prev=has_prev, page=page)


@admin_blueprint.route('/update-user-status', methods=['POST'])
@login_required
@admin_required
def update_user_status():
    user_id = request.form['user_id']
    print(user_id)

    # get user
    user = User.query.get(user_id)
    if user is None:
        flash('username wrong!', 'error')
        return redirect(url_for('admin.admin'))
    elif user.username == 'admin':
        flash("user admin can't deactivated", 'error')
        return redirect(url_for('admin.admin'))

    user.is_active = not user.is_active
    db.session.commit()

    return redirect(url_for('admin.admin'))
