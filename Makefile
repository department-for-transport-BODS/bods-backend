ifneq (,$(wildcard ./config/.env))
    include ./config/.env
    export
endif

ENV?=local
FUNC?=GenerateSiriVmLambda
DIRNAME=`basename ${PWD}`
PG_EXEC=psql "host=localhost port=$(POSTGRES_PORT) user=$(POSTGRES_USER) password=$(POSTGRES_PASSWORD) gssencmode='disable'

cmd-exists-%:
	@hash $(*) > /dev/null 2>&1 || \
		(echo "ERROR: '$(*)' must be installed and available on your PATH."; exit 1)

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/[:].*[##]/:/'

start-services: ## Start the Docker container services
	docker-compose --compatibility --env-file ./config/.env up --build --force-recreate

stop-services: ## Stop the Docker container services
	docker-compose --env-file ./config/.env down

clean-services: ## Stop and remove all related Docker container services
	docker-compose --env-file ./config/.env down
	docker rm -f postgres pgadmin 2>/dev/null
	docker volume rm ${DIRNAME}_postgres-data 2>/dev/null

generate-models: ## Generate models.py from BODs DB (DB must be running)
	python model_gen.py

build-backend: generate-models ## Build the backend functions using sam
	@samlocal build
	python localstack/scripts/bootstrap_layers.py 

build-backend-sync: ## Build the backend api using sam and keep contents synced for test
	@nodemon --watch './src/**/*.py' --signal SIGTERM --exec 'sam' build -e "py"

deploy-backend: ## Deploy the backend functions to target environment using sam
	@samlocal deploy --config-env=$(ENV) --resolve-s3

run-backend-function: ## Runs a standalone backend function locally using sam (default: GenerateSiriVmLambda)
	@sam local invoke $(FUNC)

run-timetables-etl: ## Start execution of the timetables etl stepfunction
	$(eval CURRENT_STEP_FUNCTION_EXECUTION_ARN := $(shell ./localstack/scripts/run-timetables-etl.sh))
	@echo $(CURRENT_STEP_FUNCTION_EXECUTION_ARN) > current_execution_arn
	@echo "Execution ARN set to: $(CURRENT_STEP_FUNCTION_EXECUTION_ARN)"

check-timetables-etl: ## Check the status of the last timetables stepfunction execution
	./localstack/scripts/check-timetables-etl.sh "$$(cat current_execution_arn)"

run-db-initialise: cmd-exists-psql ## Initialise the database with users/roles and schema
	@echo "Initialising the database..."
	@for file in `find ./sql/local -type f | sort | cut -c3-`; do ${PG_EXEC}" -f $$file; done

run-db-migrations: cmd-exists-psql ## Run the database migrations found under ./sql
	@echo "Running available database migrations..."
	@for file in `find ./sql -type f -depth 1 | sort | cut -c3-`; do ${PG_EXEC} dbname=$(POSTGRES_DB)" -f $$file; done

run-db-destroy: cmd-exists-psql ## Delete the database
	@echo "Destroying the database..."
	@${PG_EXEC}" -c "DROP DATABASE $(POSTGRES_DB) WITH (FORCE); "