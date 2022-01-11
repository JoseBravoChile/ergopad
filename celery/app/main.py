from celery import Celery

celery = Celery("tasks", broker="redis://redis:6379/0")

# https://www.distributedpython.com/2018/05/29/task-routing/
# celery.conf.task_routes = {"tasks.*": "task-queue"}

### INIT
@celery.task(acks_late=True)
def hello(word: str) -> str:
    return f"Hello, {word}"
