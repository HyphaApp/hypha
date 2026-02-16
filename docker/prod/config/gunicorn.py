import multiprocessing
import os

wsgi_app = "hypha.wsgi:application"
bind = "0.0.0.0:8000"

errorlog = "-"  # '-' logs to stderr
accesslog = "-"  # '-' logs to stdout
access_log_format = (
    "%(h)s %(l)s %(u)s %(t)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s' in %(D)sµs"  # noqa: E501
)

worker_tmp_dir = "/dev/shm"
worker_class = "gthread"
workers = int(os.getenv("PYTHON_WORKERS", multiprocessing.cpu_count() * 2))
threads = int(os.getenv("PYTHON_THREADS", 1))
timeout = int(os.getenv("PYTHON_TIMEOUT", 120))
