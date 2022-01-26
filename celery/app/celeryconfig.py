result_backend = 'redis://redis:6379/1'
task_track_started = True
# imports = ['tasks.hello']
task_ignore_result = False
task_serializer = 'json'
# result_serializer = 'json'
accept_content = ['application/json', 'json', 'yaml']
CELERYD_LOG_LEVEL = "INFO"