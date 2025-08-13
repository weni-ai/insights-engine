#!/bin/bash

export GUNICORN_APP=${GUNICORN_APP:-"insights.wsgi"}
export GUNICORN_CONF=${GUNICORN_CONF:-"${PROJECT_PATH}/gunicorn.conf.py"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
export CELERY_MAX_WORKERS=${CELERY_MAX_WORKERS:-'4'}
export CELERY_BEAT_DATABASE_FILE=${CELERY_BEAT_DATABASE_FILE:-'/tmp/celery_beat_database'}

do_gosu(){
    user="$1"
    shift 1

    is_exec="false"
    if [ "$1" = "exec" ]; then
        is_exec="true"
        shift 1
    fi

    if [ "$(id -u)" = "0" ]; then
        if [ "${is_exec}" = "true" ]; then
            exec gosu "${user}" "$@"
        else
            gosu "${user}" "$@"
            return "$?"
        fi
    else
        if [ "${is_exec}" = "true" ]; then
            exec "$@"
        else
            eval '"$@"'
            return "$?"
        fi
    fi
}


if [[ "start" == "$1" ]]; then
    echo "Run collectstatic"
    do_gosu "${PROJECT_USER}:${PROJECT_GROUP}" python manage.py collectstatic --noinput
    echo "Starting gunicorn workers"
    do_gosu "${PROJECT_USER}:${PROJECT_GROUP}" exec gunicorn "${GUNICORN_APP}" \
      --name="${APPLICATION_NAME}" \
      --chdir="${PROJECT_PATH}" \
      --bind=0.0.0.0:8000 \
      -c "${GUNICORN_CONF}"
elif [[ "celery-worker" == "$1" ]]; then
    celery_queue="celery"
    if [ "${2}" ] ; then
        celery_queue="${2}"
    fi
    do_gosu "${PROJECT_USER}:${PROJECT_GROUP}" exec celery \
        -A temba --workdir="${PROJECT_PATH}" worker \
        -Q "${celery_queue}" \
        -O fair \
        -l "${LOG_LEVEL}" \
        --autoscale="${CELERY_MAX_WORKERS},1"
elif [[ "celery-beat" == "$1" ]]; then
    do_gosu "${PROJECT_USER}:${PROJECT_GROUP}" exec celery \
        -A temba --workdir="${PROJECT_PATH}" beat \
        --loglevel="${LOG_LEVEL}" \
        -s "${CELERY_BEAT_DATABASE_FILE}"
fi

exec "$@"
