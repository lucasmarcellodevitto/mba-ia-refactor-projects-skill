from datetime import timedelta

from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from repositories.category_repository import CategoryRepository
from services.errors import NotFoundError
from utils.helpers import calculate_percentage, utcnow

RECENT_ACTIVITY_WINDOW_DAYS = 7


class ReportService:
    def __init__(self, task_repo=None, user_repo=None, category_repo=None):
        self.task_repo = task_repo or TaskRepository()
        self.user_repo = user_repo or UserRepository()
        self.category_repo = category_repo or CategoryRepository()

    def summary_report(self):
        now = utcnow()

        all_tasks = self.task_repo.get_all()
        overdue_list = []
        for t in all_tasks:
            if t.is_overdue():
                overdue_list.append({
                    'id': t.id,
                    'title': t.title,
                    'due_date': str(t.due_date),
                    'days_overdue': (now - t.due_date).days,
                })

        since = now - timedelta(days=RECENT_ACTIVITY_WINDOW_DAYS)

        users = self.user_repo.get_all()
        total_by_user = self.task_repo.count_by_user()
        done_by_user = self.task_repo.count_done_by_user()
        user_stats = []
        for u in users:
            total = total_by_user.get(u.id, 0)
            completed = done_by_user.get(u.id, 0)
            user_stats.append({
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total),
            })

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': self.task_repo.count_all(),
                'total_users': self.user_repo.count_all(),
                'total_categories': self.category_repo.count_all(),
            },
            'tasks_by_status': {
                'pending': self.task_repo.count_by_status('pending'),
                'in_progress': self.task_repo.count_by_status('in_progress'),
                'done': self.task_repo.count_by_status('done'),
                'cancelled': self.task_repo.count_by_status('cancelled'),
            },
            'tasks_by_priority': {
                'critical': self.task_repo.count_by_priority(1),
                'high': self.task_repo.count_by_priority(2),
                'medium': self.task_repo.count_by_priority(3),
                'low': self.task_repo.count_by_priority(4),
                'minimal': self.task_repo.count_by_priority(5),
            },
            'overdue': {
                'count': len(overdue_list),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': self.task_repo.count_created_since(since),
                'tasks_completed_last_7_days': self.task_repo.count_completed_since(since),
            },
            'user_productivity': user_stats,
        }

    def user_report(self, user_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = self.task_repo.get_by_user_id(user_id)

        total = len(tasks)
        done = pending = in_progress = cancelled = overdue = high_priority = 0

        for t in tasks:
            if t.status == 'done':
                done += 1
            elif t.status == 'pending':
                pending += 1
            elif t.status == 'in_progress':
                in_progress += 1
            elif t.status == 'cancelled':
                cancelled += 1

            if t.priority <= 2:
                high_priority += 1

            if t.is_overdue():
                overdue += 1

        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': calculate_percentage(done, total),
            },
        }
