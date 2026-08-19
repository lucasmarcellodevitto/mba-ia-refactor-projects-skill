from database import db
from models.user import User


class UserRepository:
    def get_all(self):
        return User.query.all()

    def get_by_id(self, user_id):
        return db.session.get(User, user_id)

    def get_by_ids(self, ids):
        if not ids:
            return []
        return User.query.filter(User.id.in_(ids)).all()

    def get_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def count_all(self):
        return User.query.count()

    def add(self, user):
        db.session.add(user)

    def delete(self, user):
        db.session.delete(user)

    def commit(self):
        db.session.commit()

    def rollback(self):
        db.session.rollback()
