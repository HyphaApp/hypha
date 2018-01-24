from datetime import datetime

from fabric.api import lcd, roles, runs_once, run, local, env, prompt, get


env.roledefs = {
    'production': [],
    'pre-production': {
        'hosts': ['otfpreprod@staging-1-a.bmyrk.torchbox.net'],
        'config': {
            'env_name': 'pre-production',
            'remote_db_name': 'otfpreprod',
            'local_db_name': 'opentech',
            'remote_dump_path': '/var/www/otfpreprod/tmp/',
            'local_dump_path': '/tmp/',
        }
    },
    'staging': {
        'hosts': ['otfstaging@staging-1-a.bmyrk.torchbox.net'],
        'config': {
            'env_name': 'staging',
            'remote_db_name': 'otfstaging',
            'local_db_name': 'opentech',
            'remote_dump_path': '/var/www/otfstaging/tmp/',
            'local_dump_path': '/tmp/',
        },
    },
    'dev': {
        'hosts': ['otfdev@staging-1-a.bmyrk.torchbox.net'],
        'config': {
            'env_name': 'dev',
            'remote_db_name': 'otfdev',
            'local_db_name': 'opentech',
            'remote_dump_path': '/var/www/otfdev/tmp/',
            'local_dump_path': '/tmp/',
        },
    },
}


@roles('production')
def deploy_production():
    # Remove this line when you're happy that this task is correct
    raise RuntimeError("Please check the fabfile before using it")

    _deploy()


@runs_once
@roles('production')
def pull_production_data():
    # Remove this line when you're happy that this task is correct
    raise RuntimeError("Please check the fabfile before using it")

    _pull_data_wrapper()


@runs_once
@roles('production')
def pull_production_media():
    _pull_media()


@roles('staging')
def deploy_staging():
    _deploy()


@runs_once
@roles('staging')
def pull_staging_data():
    _pull_data_wrapper()


@runs_once
@roles('staging')
def pull_staging_media():
    _pull_media()


@roles('pre-production')
def deploy_pre_production():
    _deploy()


@runs_once
@roles('pre-production')
def pull_pre_production_data():
    _pull_data_wrapper()


@runs_once
@roles('pre-production')
def pull_pre_production_media():
    _pull_media()


@roles('dev')
def deploy_dev():
    _deploy('develop')


@runs_once
@roles('dev')
def pull_dev_data():
    _pull_data_wrapper()


@runs_once
@roles('dev')
def pull_dev_media():
    _pull_media()


def _deploy(branch='master'):
    """Generic deployment tasks. Inherits the active role"""

    _build_static(branch)
    _deploy_static()

    run('git pull')
    run('pip install -r requirements.txt')
    _run_migrate()
    run('django-admin collectstatic --noinput')

    # 'restart' should be an alias to a script that restarts the web server
    run('restart')

    _post_deploy()


def _pull_data_wrapper():
    role = env.effective_roles[0]
    config = env.roledefs[role]['config']

    _pull_data(
        env_name=config['env_name'],
        remote_db_name=config['remote_db_name'],
        local_db_name=config['local_db_name'],
        remote_dump_path=config['remote_dump_path'],
        local_dump_path=config['local_dump_path'],
    )


@runs_once
def _pull_media():
    local('rsync -avz %s:\'%s\' /vagrant/media/' % (env['host_string'], '$CFG_MEDIA_DIR'))


@runs_once
def _pull_data(env_name, remote_db_name, local_db_name, remote_dump_path, local_dump_path):
    timestamp = datetime.now().strftime('%Y%m%d-%I%M%S')

    filename = '.'.join([env_name, remote_db_name, timestamp, 'sql'])
    remote_filename = remote_dump_path + filename
    local_filename = local_dump_path + filename

    params = {
        'remote_db_name': remote_db_name,
        'remote_filename': remote_filename,
        'local_db_name': local_db_name,
        'local_filename': local_filename,
    }

    # Dump/download database from server
    run('pg_dump {remote_db_name} -xOf {remote_filename}'.format(**params))
    run('gzip {remote_filename}'.format(**params))
    get('{remote_filename}.gz'.format(**params), '{local_filename}.gz'.format(**params))
    run('rm {remote_filename}.gz'.format(**params))

    # Load database locally
    local('gunzip {local_filename}.gz'.format(**params))
    _restore_db(local_db_name, local_filename)


def _restore_db(local_db_name, local_dump_path):
    params = {
        'local_db_name': local_db_name,
        'local_dump_path': local_dump_path,
    }

    local('dropdb {local_db_name}'.format(**params))
    local('createdb {local_db_name}'.format(**params))
    local('psql {local_db_name} -f {local_dump_path}'.format(**params))
    local('rm {local_dump_path}'.format(**params))

    newsuperuser = prompt(
        'Any superuser accounts you previously created locally will'
        ' have been wiped. Do you wish to create a new superuser? (Y/n): ',
        default="Y"
    )
    if newsuperuser.strip().lower() == 'y':
        local('django-admin createsuperuser')


@runs_once
def _run_migrate():
    # Run migrations
    run('django-admin migrate --noinput')
    # Create a table for database cache backend
    run('django-admin createcachetable')


@runs_once
def _post_deploy():
    # clear frontend cache only on production
    if 'production' in env.effective_roles:
        run(
            'for host in $(echo $CFG_HOSTNAMES | tr \',\' \' \'); do echo "Purge cache for $host";'
            'ats-cache-purge $host; '
            'done'
        )

    # update search index
    run('django-admin update_index')


@runs_once
def _build_static(build_branch='master'):
    # Build a specific branch
    current_branch = local('git rev-parse --abbrev-ref HEAD', capture=True)
    if current_branch != build_branch:
        raise RuntimeError("Please switch to '{}' before deploying".format(build_branch))

    local('git pull')
    with lcd('/vagrant/opentech/static_src/'):
        local('yarn build:prod --silent')


@runs_once
def _deploy_static():
    # Copy the compiled static files to the server
    local("rsync -avz /vagrant/opentech/static_compiled %s:'../app/opentech/'" % (env['host_string']))
