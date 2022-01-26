from celery import Celery

celery = Celery("tasks", broker="redis://redis:6379/0")

#region LOGGING
import logging
levelname = (logging.WARN, logging.DEBUG)[DEBUG]
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', levelname=levelname)

import inspect
myself = lambda: inspect.stack()[1][3]
#endregion LOGGING

#region ROUTING
# https://www.distributedpython.com/2018/05/29/task-routing/
# celery.conf.task_routes = {"tasks.*": "task-queue"}

# celery worker -E -l INFO -n workerA -Q for_task_A
# celery worker -E -l INFO -n workerB -Q for_task_B
CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('for_task_A', Exchange('for_task_A'), routing_key='for_task_A'),
    Queue('for_task_B', Exchange('for_task_B'), routing_key='for_task_B'),
)

CELERY_ROUTES = {
    'my_taskA': {'queue': 'for_task_A', 'routing_key': 'for_task_A'},
    'my_taskB': {'queue': 'for_task_B', 'routing_key': 'for_task_B'},
}
#endregion ROUTING

class BaseTask(app.Task):
    """Abstract base class for all tasks in my app."""
    abstract = True

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Log the exceptions to sentry at retry."""
        sentrycli.captureException(exc)
        super(BaseTask, self).on_retry(exc, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log the exceptions to sentry."""
        sentrycli.captureException(exc)
        super(BaseTask, self).on_failure(exc, task_id, args, kwargs, einfo)

def backoff(attempts):
    return 2**attempts

@celery.task(acks_late=True, bind=True, default_retry_delay=300, max_retries=5, base=BaseTask)
def hello(word: str) -> str:
    try:
        return f"Hello, {word}"
    except Exception as e:
        countdown = backoff(self.request.retries)
        logging.error(f'{myself()}: {e}; retry in {countdown}s')
        self.retry(countdown=countdown, exc=e)

