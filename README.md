# FastAPI Template Generator

This repository provides a [FastAPI](https://fastapi.tiangolo.com/) base stack:

- Runnable from VSCode launch with or without docker containers
- Generic [Firestore](https://firebase.google.com/docs/firestore?hl=fr) client (authentication with [ADC](https://cloud.google.com/docs/authentication/provide-credentials-adc?hl=fr))
- Generic [PostgreSQL](https://www.postgresql.org/about/) async client wrapped with [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy 2.0)

The template is

- Based on [cookiecutter](https://www.cookiecutter.io/)
- Auto-pushable on Github when generated
- Auto-deployable on [Cloud Run](https://cloud.google.com/run).

It assumes the template is pushed on a separate Github repository

## Installation

- Install dependencies

  ```bash
  cd fastapi-generator
  python3 -m pip install -r requirements.txt
  ```

- (Optional): Add a github access token to .env file if you want the branch protection to be automated at generation

```bash
# .env content ...
GITHUB_ACCESS_TOKEN="<PERSONAL_ACCESS_TOKEN>"
```

## Generate Project

```bash
cookiecutter fastapi-generator/app   # Will ask your needs from cookiecutter.json
```

- **'repository_name'** allows you to specify an empty-existing Git repository to push the template on.

  ```bash
  <github_username>/<repo_name>  # Required format

  # 1. Ensure you have corrects SSH rights & access

  # 2. This will also set branch protection if you specified GITHUB_ACCESS_TOKEN variable in .env
  # Change settings as your convenience in hooks_modules/branch_protection.json
  ```

- **'project_name'** is the name on the top of ReadMe.

- **'project_slug'** is the name of the generated folder

- **'description'** will be added under the project name in the ReadMe.

- **'maintainer'** has an informativ goal (not used in the template)

- **'database'** make you choose which type of database will be provided (Firestore, PostgreSQL with SQLModel, or Both)

- **'as_container'** provide local dockerization and auto deploy on Cloud Run

- **'gcloud_project'** is the GCP project ID on which the project will be deployed

## CICD

Github action is provided for testing the template generation, install dependencies, runs dev server & unit tests.

You can try github actions locally from root folder using [act](https://nektosact.com/):

```bash
act -j test-run-template --rm -W .github/workflows/template-generation.yaml
```

## TODO

Deployment:

- Add a specific database user and not postgres
