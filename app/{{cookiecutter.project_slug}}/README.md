# {{cookiecutter.project_name}}

{{ '=' * cookiecutter.project_name|length }}

## Description

{{cookiecutter.description}}

[GCP Project](https://console.cloud.google.com/home/dashboard?authuser=0&project={{cookiecutter.gcloud_project}}&supportedpurview=project)

## Template Stack

- [FastApi](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [SQLAlchemy 2](https://docs.sqlalchemy.org/en/20/)
- [Firestore client](https://firebase.google.com/docs/firestore)
- [Async PostgreSQL client](https://github.com/MagicStack/asyncpg)

## Project Setup

- Install [Poetry](https://python-poetry.org/docs/)

- Set config for venv in local

  ```sh
  poetry config virtualenvs.in-project true
  poetry env use 3.11
  poetry shell
  poetry install
  ```

- (Postgres only) Create and run required databases

  ```bash
  docker compose up -d
  ```

- Apply migrations

  ```sh
  alembic upgrade head
  ```

### Run locally

```sh
# WITHOUT DOCKER (Guess ADC from env)
uvicorn app.main:app --reload          # Or from VSCode launcher

# WITH DOCKER
Use the launch.json configuration to build and run the container
```

## Tests

```sh
poetry run pytest --cov=app --cov-report=term     # Uses SQLALCHEMY_DATABASE_URI in pyproject.toml
```

## Application Structure

```bash
{{cookiecutter.project_slug}}
│
├── .cloudbuild                    - Cloud Build configuration
│   └── cloudbuild.yaml
│
├── .github                        
│   └── workflows                  - Github Actions
│
├── .vscode
│   ├── launch.json                - Launch to execute the app
│   └── tasks.json                 - For dockerized launch
│
├── Dockerfile.prod                - Used to build and deploy on Cloud Run
│
├── alembic.ini                    - Local Database configuration
│
├── app                            - Web stuffs
│   ├── api                           - Global deps & routing
│   └── core                          
│      ├── google_apis                  - Google API's utils
│      ├── cloud_logging.py             - Logging wrapper
│      ├── config.py                    - Global app configuration
│      └── google_clients.py            - Google API's client builders
│
│   ├── firestore                     - CRUD, Endpoints, Models for Firestore
│   ├── models                        - Common models for Firestore or PostgreSQL
│   ├── sqlmodel                      - CRUD, Endpoints, Models for SQLAlchemy
│   ├── main.py                       - Entrypoint, app instanciation & middleware
│   └── middleware.py                 - Middleware definitions (Metric, Logs, Exceptions)
│
├── docker-compose.yml             - Provide database local containers
│
├── main.tf                        - Terraform configuration for deployment
│
├── migrations                     - PostgreSQL migrations
│
├── pyproject.toml
│
├── setup.cfg                      - Flake8 configuration
│
└── tests
```

## Deployment

:warning: Everything under this section assumes you specified a repository to push to, and choosed 'yes' to "as_container" question. Otherwise update the main.tf according yo your needs before running  :warning:

### Initialisation

To deploy the infrastructure, make sure ADC is configured correctly.

The main.tf will deploy:

- Image into the Artifact Registry used by Cloud Run
- Cloud Run service
- Secret in Secret Manager
- Cloud Build Trigger linked to the repository specified

Additionally, it will deploy a Cloud SQL and/or Firestore database according to you database choice.
You may need additional IAM roles to deploy databases

```bash

# Ensure your .env content is the deployed version before running
cd {{ cookiecutter.project_slug }}
terraform init
terraform apply

```

Once deployment is done:

- [Connect your repository to Cloud Build](https://console.cloud.google.com/cloud-build/repositories/1st-gen?authuser=0&project={{cookiecutter.gcloud_project}}&supportedpurview=project)
- [Add .env content into secret version](https://console.cloud.google.com/security/secret-manager/secret/{{cookiecutter.project_slug.replace('_','-')}}/versions?authuser=0&project={{cookiecutter.gcloud_project}}&supportedpurview=project)

Cloud Build is now ready to deploy new Cloud Run revision after each push

## CI/CD

### CI with Github Actions

Use .github/workflows/lint.yaml __by enabling Github Actions API__ in your repository

This will run linting for every Pull Request on develop, uat and main branches

### CD with Cloud Build & Cloud Run

.cloudbuild/cloudbuild.yaml is used automatically to deploy to Cloud Run according to your Cloud Build trigger configuration

*Requirements*:

- From the trigger created by Terraform, give Github repository access to Cloud Build

- Copy .env into the secret '{{ cookiecutter.project_slug.replace('_', '-') }}' to ensure Cloud Build will have the correct environement.

## Api docs

- [Swagger](http://localhost:8000/api/docs)

## Maintainers

{{cookiecutter.maintainer}}
