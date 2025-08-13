ENVIRONMENT_VARS_FILE := .env
IS_PRODUCTION ?= false
CHECK_ENVIRONMENT := true


# Commands

help:
	@cat Makefile-help.txt
	@exit 0

## Environment
install:
	@make check_environment
	@make migrate
	@make dev_up
	@python manage.py runserver

# @make add_initial_data

test:
	@coverage run manage.py test
	@coverage report -m

lint:
	@flake8
	@black .
	@isort .

## Docker

dev_up:
	@docker compose -f docker/docker-compose.yaml up -d postgres redis

dev_down:
	@docker compose -f docker/docker-compose.yaml down

## Database

add_initial_data:
	@python manage.py loaddata insights/fixtures/*.json

migrate:
	@python manage.py migrate

migrations:
	@python manage.py makemigrations
	@make migrate

## CI
pre-commit-install:
	@pre-commit install

pre-commit-run:
	@pre-commit run --all-files


# Utils

## Colors
SUCCESS = \033[0;32m
INFO = \033[0;36m
WARNING = \033[0;33m
DANGER = \033[0;31m
NC = \033[0m

create_environment_vars_file:
	@echo "${INFO}Creating enviroment file...${NC}"
	@echo "SECRET_KEY=SK" > "${ENVIRONMENT_VARS_FILE}"
	@echo "DEBUG=true" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "DATABASE_URL=postgres://insights:insights@localhost:5432/insights" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "OIDC_RP_SERVER_URL=''" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "OIDC_RP_REALM_NAME=''" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "OIDC_OP_JWKS_ENDPOINT=''" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "OIDC_RP_CLIENT_ID=''" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "OIDC_RP_CLIENT_SECRET=''" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "OIDC_OP_AUTHORIZATION_ENDPOINT=''" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "OIDC_OP_TOKEN_ENDPOINT=''" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "OIDC_OP_USER_ENDPOINT=''" >> "${ENVIRONMENT_VARS_FILE}"
	@echo "${SUCCESS}✔${NC} Settings file created"
	install_development_requirements:
	@echo "${INFO}Installing development requirements...${NC}"
	@poetry install
	@echo "${SUCCESS}✔${NC} Development requirements installed"

install_production_requirements:
	@echo "${INFO}Installing production requirements...${NC}"
	@POETRY_VIRTUALENVS_CREATE=false poetry install --no-dev
	@echo "${SUCCESS}✔${NC} Requirements installed"

install_requirements:
	@if [ ${IS_PRODUCTION} = true ]; \
		then make install_production_requirements; \
		else make install_development_requirements; fi

check_environment:
	@type poetry || (echo "${DANGER}☓${NC} Install poetry to continue..." && exit 1)
	@echo "${SUCCESS}✔${NC} poetry installed"
	@if [ ! -f "${ENVIRONMENT_VARS_FILE}" ] && [ ${IS_PRODUCTION} = false ]; \
		then make create_environment_vars_file; \
	fi
	@make install_requirements
	@make pre-commit-install
	@echo "${SUCCESS}✔${NC} Environment checked"