from flask_login import UserMixin
from . import db



class User(db.Model, UserMixin):
  __tablename__ = 'user'
  user_id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
  username = db.Column(db.String, nullable=False)
  email = db.Column(db.String, unique=True, nullable=False)
  password = db.Column(db.String, nullable=False)
  level = db.Column(db.CHAR, nullable=False)
  def get_id(self):
    return (self.user_id)