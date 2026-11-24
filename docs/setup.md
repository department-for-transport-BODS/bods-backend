# Prerequisites
* [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
* [Node (v18.x.x) / npm (v9.x.x)](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
* [nodemon (npm Package)](https://www.npmjs.com/package//nodemon)
* [PostgreSQL Client (psql)](https://www.postgresql.org/download/)
* [Docker Desktop](https://www.docker.com/get-started/) **or another container runtime of your choosing**

## Installation

### Step 1: Set up docker compose

Environment configuration when using Docker Compose is achieved using a `.env`
file that is passed to the docker containers. A template for the `.env` file is
provided in the repository (`.env.template`).

First copy the `.env.template` file to `.env` within the _config/_ 
directory:

```sh
# Assuming you're in the pdbrd-app root directory
cp .env.template .env
```

### Step 2: Start supporting services

There are different options available when it comes to running the services 
locally. For database administration, this is managed using the previously 
configured docker compose, and both a PostgreSQL, pgAdmin, and localstack 
container instance can be managed easily by running a combination of the 
following:

```sh
# Start up container services for backend data storage
make start-services

# Stop container services for backend data storage
make stop-services

# Stop and remove all related backend data storage container services
make clean-services
```

As part of the startup of PostgreSQL, the initial project database will be created 
with roles defined within the `./sql/local` directory.

### Step 3: Initialise the database schema

Whilst the application database and users themselves are created as part of 
the PostgreSQL startup, creation of the schema and any further database 
migrations requires that a subsequent _make_ command is executed:

```sh
# Run all .sql scripts sequentially against the application database
make run-db-migrations
```

This will fully initialise the database and populate it with the necessary
tables/triggers that allow for storage of data by the application.


### Step 4: Run the application backend functions

The backend functions are written in Python and use AWS SAM for deployment into 
any target environment. For local testing AWS SAM provides an option to run
these services locally (using Docker on the backend, although this process
is hidden from the end user).

In order to start these services up, it is necessary to run:

```sh
# Build the backend functions in a one time operation, with no monitoring of changes
# This action will need to be repeated when changes are made to underlying code
make build-backend

# Alternatively, in a separate terminal, build the backend functions and set a watcher
# to rebuild automatically with changes on ./src
make build-backend-sync

# Run the desired backend function. Substitute $FUNCTION_NAME with the actual name of the
# function as per SAM template, e.g. GenerateSiriVmLambda
FUNC=$FUNCTION_NAME make run-backend-function
```

It is advisable (and at times necessary) to run each service in separate 
terminals to be able to take full advantage of any debug logging that may
occur as a result of running these applications. It is worth noting that 
changes to the underlying codebase should be reflected in the already
running application(s), without the need for additional rebuilding.