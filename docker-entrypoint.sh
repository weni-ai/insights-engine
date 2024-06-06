#!/bin/bash

export GUNICORN_APP=${GUNICORN_APP:-"insights.wsgi"}
export GUNICORN_CONF=${GUNICORN_CONF:-"${PROJECT_PATH}/gunicorn.conf.py"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

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
fi

exec "$@"
