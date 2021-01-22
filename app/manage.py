from functools import wraps
from flask import Flask, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_blog.db'
    app.secret_key = '**77Gh!2*(0%'
    app.config['UPLOAD_FOLDER'] = './static/uploads'
    # limit file upload size
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    from app.admin import models
    from app.post import models

    db.init_app(app)
    migrate.init_app(app, db)

    from app.admin.views import admin_blueprint
    from app.post.views import post_blueprint
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(post_blueprint)

    return app


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username') is None:
            session.clear()
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            session.clear()
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function
