#!/bin/bash
# This script is installed in the Docker "app" image and is executed when a container is started from the image.
# todo: could add env to the path, activate doesn't seem to function? Also add unbound to the path.
set -exvu

# Enter venv
source ${APP_PATH}/.venv/bin/activate

PATH=/opt/unbound2/sbin/:$PATH

# Start Unbound and ensure it is the default resolver. LDNS-DANE uses this.
sudo env "PATH=$PATH" unbound-control start
sudo env "PATH=$PATH" unbound-control status

# Sanity check our DNS configuration. The default resolver should be DNSSEC
# capable. If not LDNS-DANE will fail to verify domains. Internet.NL calls out
# to LDNS-DANE so this needs to work for Internet.NL tests to work properly.
ldns-dane -n -T verify ${LDNS_DANE_VALIDATION_DOMAIN} 443 || echo >&2 "ERROR: Please run this container with --dns 127.0.0.1"

# Use settings.py with defaults
rm -f ${APP_PATH}/internetnl/settings.py
cp ${APP_PATH}/internetnl/settings-dist.py ${APP_PATH}/internetnl/settings.py

# configure Django logging
cat << EOF >> ${APP_PATH}/internetnl/settings.py
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': 'django.log',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }
EOF

# Switch to app directory
cd ${APP_PATH}

# Prepare translations for use
python manage.py compilemessages

# Check for database connectivity
docker/postgres-ping.sh postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Prepare the database for use
python ./manage.py migrate

# Optional steps for the batch dev environment
if [ ${ENABLE_BATCH} == "True" ]; then
    # create indexes
    python ./manage.py api_create_db_indexes
    # guarantee the existence of a test_user in the db
    python ./manage.py api_users register -u test_user -n test_user -o test_user -e test_user || :
    # generate API documentation
    cp ${APP_PATH}/internetnl/batch_api_doc_conf{_dist,}.py
    ln -sf ${APP_PATH}/checks/static ${APP_PATH}/static # static/ is not served, checks/static is
    python ./manage.py api_generate_doc # creates openapi.yaml in static/
fi

# Start Celery
# Todo: should this just start the celery workers via systemd while we're at it?
# queues/settings taken from the shipped config file
if [ ${ENABLE_BATCH} == "True" ]; then
    celery -A internetnl multi start \
	db_worker slow_db_worker worker_slow batch_slow batch_main batch_callback celery default nassl_worker ipv6_worker mail_worker web_worker resolv_worker dnssec_worker \
	-c 1 -c:1-6 1 -Q:1 db_worker -Q:2 slow_db_worker -Q:3 worker_slow -Q:4 batch_slow -Q:5 celery -Q:6 default -c:7 50 -Q:7 batch_main -c:8 2 -Q:8 batch_callback -c:9 150 -Q:9 nassl_worker -c:10 20 -Q:10 ipv6_worker -c:11 20 -Q:11 mail_worker -c:12 20 -Q:12 web_worker -c:13 50 -Q:13 resolv_worker -c:14 20 -Q:14 dnssec_worker \
        -l info --without-gossip --time-limit=300 --pidfile='/app/%n.pid' \
        --logfile='/app/%n%I.log' -P eventlet &
else
    celery -A internetnl multi start \
        worker db_worker slow_db_worker nassl_worker ipv6_worker mail_worker web_worker resolv_worker dnssec_worker \
        -c:1 10 -c:2 3 -Q:2 db_worker -c:3 3 -Q:3 slow_db_worker -c:4 150 -Q:4 nassl_worker -c:5 20 -Q:5 ipv6_worker -c:6 20 -Q:6 mail_worker -c:7 20 -Q:7 web_worker -c:8 50 -Q:8 resolv_worker -c:9 20 -Q:9 dnssec_worker \
        -l info --without-gossip --time-limit=300 --pidfile='/app/%n.pid' \
        --logfile='/app/%n%I.log' -P eventlet &
fi

# Start Celery Beat
celery -A internetnl beat &

# Wait a little while for all 3 Celery worker groups to become ready
if [ ${ENABLE_BATCH} == "True" ]; then
    docker/celery-ping.sh 7 20
else
    docker/celery-ping.sh 3
fi

# Tail the Celery log files so that they appear in Docker logs output
tail -F -n 1000 *.log &

# Make the frontend
make frontend

# Start the Django web server
python ./manage.py ${RUN_SERVER_CMD} 0.0.0.0:8080
