from app.manage import db
from passlib.hash import pbkdf2_sha256 as sha256


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), nullable=False, unique=True, )
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=True)
    role = db.Column(db.String, default='user')
    is_active = db.Column(db.Boolean, nullable=False, default=False)

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

    def __repr__(self):
        return '<user {}>'.format(self.username)
