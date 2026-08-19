from database import db
from models.task import Task


class TaskRepository:
    def get_all(self):
        return Task.query.all()

    def get_by_id(self, task_id):
        return db.session.get(Task, task_id)

    def get_by_user_id(self, user_id):
        return Task.query.filter_by(user_id=user_id).all()

    def search(self, query=None, status=None, priority=None, user_id=None):
        q = Task.query

        if query:
            q = q.filter(
                db.or_(
                    Task.title.like(f'%{query}%'),
                    Task.description.like(f'%{query}%'),
                )
            )
        if status:
            q = q.filter(Task.status == status)
        if priority is not None:
            q = q.filter(Task.priority == priority)
        if user_id is not None:
            q = q.filter(Task.user_id == user_id)

        return q.all()

    def count_all(self):
        return Task.query.count()

    def count_by_status(self, status):
        return Task.query.filter_by(status=status).count()

    def count_by_priority(self, priority):
        return Task.query.filter_by(priority=priority).count()

    def count_created_since(self, since):
        return Task.query.filter(Task.created_at >= since).count()

    def count_completed_since(self, since):
        return Task.query.filter(
            Task.status == 'done', Task.updated_at >= since
        ).count()

    def count_by_user(self):
        """Retorna {user_id: quantidade de tasks} em uma única query agregada."""
        rows = (
            db.session.query(Task.user_id, db.func.count(Task.id))
            .group_by(Task.user_id)
            .all()
        )
        return {user_id: count for user_id, count in rows if user_id is not None}

    def count_done_by_user(self):
        """Retorna {user_id: quantidade de tasks concluídas} em uma única query agregada."""
        rows = (
            db.session.query(Task.user_id, db.func.count(Task.id))
            .filter(Task.status == 'done')
            .group_by(Task.user_id)
            .all()
        )
        return {user_id: count for user_id, count in rows if user_id is not None}

    def count_by_category(self):
        """Retorna {category_id: quantidade de tasks} em uma única query agregada."""
        rows = (
            db.session.query(Task.category_id, db.func.count(Task.id))
            .group_by(Task.category_id)
            .all()
        )
        return {
            category_id: count
            for category_id, count in rows
            if category_id is not None
        }

    def add(self, task):
        db.session.add(task)

    def delete(self, task):
        db.session.delete(task)

    def commit(self):
        db.session.commit()

    def rollback(self):
        db.session.rollback()
