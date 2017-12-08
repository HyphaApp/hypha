import os

from django.core.management import call_command

try:
    import uwsgi
    from uwsgidecorators import timer, cron

    print("We have a uWSGI")
    has_uwsgi = True
except ImportError:
    print("We have no uWSGI")
    has_uwsgi = False


def single_instance_command(command_name):
    """Runs command only on one instance of a uWSGI legion"""

    if uwsgi.i_am_the_lord(os.getenv("CFG_APP_NAME")):
        print("I am the lord.")
        print("Running %s" % command_name)
        call_command(command_name, interactive=False)
    else:
        print("I am not the lord.")


if has_uwsgi:
    @cron(0, 1, -1, -1, 0)
    def clearsessions(signum):
        single_instance_command('clearsessions')

    @cron(0, 0, -1, -1, 0)
    def update_index(signum):
        single_instance_command('update_index')

    @timer(300)
    def publish_scheduled_pages(cron):
        single_instance_command('publish_scheduled_pages')
