from database import db
from utils.helpers import utcnow, format_date, VALID_STATUSES, MIN_PRIORITY, MAX_PRIORITY


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': format_date(self.created_at),
            'updated_at': format_date(self.updated_at),
            'due_date': format_date(self.due_date),
            'tags': self.tags.split(',') if self.tags else [],
        }

    @staticmethod
    def validate_status(new_status):
        return new_status in VALID_STATUSES

    @staticmethod
    def validate_priority(p):
        return MIN_PRIORITY <= p <= MAX_PRIORITY

    def is_overdue(self):
        if not self.due_date:
            return False
        if self.due_date >= utcnow():
            return False
        return self.status not in ('done', 'cancelled')
