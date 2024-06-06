import multiprocessing
import os

workers = os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1)proc_name = "insights-engine"
default_proc_name = proc_name
accesslog = "-"
errorlog = "-"
capture_output = True
timeout = 120
bind = "0.0.0.0"
