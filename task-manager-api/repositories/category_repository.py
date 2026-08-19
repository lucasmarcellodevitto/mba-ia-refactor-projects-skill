from database import db
from models.category import Category


class CategoryRepository:
    def get_all(self):
        return Category.query.all()

    def get_by_id(self, category_id):
        return db.session.get(Category, category_id)

    def get_by_ids(self, ids):
        if not ids:
            return []
        return Category.query.filter(Category.id.in_(ids)).all()

    def count_all(self):
        return Category.query.count()

    def add(self, category):
        db.session.add(category)

    def delete(self, category):
        db.session.delete(category)

    def commit(self):
        db.session.commit()

    def rollback(self):
        db.session.rollback()
