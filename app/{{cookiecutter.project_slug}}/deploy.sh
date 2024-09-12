#!/bin/bash

env="dev"

while getopts ":e:" opt; do
  case $opt in
    e)
      env="$OPTARG"
      ;;
    \?)
      echo "Invalid option -$OPTARG" >&2
      exit 1
      ;;
  esac
done

if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
  echo "$env: Invalid environment. Must be one of: dev, staging, prod" >&2
  exit 1
fi

env_file=".env.$env"
if [ ! -f "$env_file" ]; then
  echo "$env_file: Environment file not found" >&2
  exit 1
fi

# Inject all .env.x variable into the script
set -o allexport
source "$env_file"
set +o allexport

echo "
Parsing $env_file 

- Environment: $ENV
- Project found: $GCLOUD_PROJECT_ID
- Region: {{cookiecutter.gcloud_region}}

Confirm deployment? (y/n): "

# Read user input
read -r confirm

if [[ "$confirm" =~ ^[Yy]$ ]]; then
  if gcloud beta builds triggers describe {{ cookiecutter.project_slug.replace('_', '-') }} \
      --project="$GCLOUD_PROJECT_ID" \
      --region="{{cookiecutter.gcloud_region}}" &>/dev/null; then
      printf "Checking $env_file new content...\n"
      # Check if env_file file is newer than secret manager content
      LATEST_SECRET_CONTENT=$(gcloud secrets versions access latest --secret="{{ cookiecutter.project_slug.replace('_', '-') }}")
      CURRENT_ENV_CONTENT=$(<$env_file)
      if [ "$LATEST_SECRET_CONTENT" != "$CURRENT_ENV_CONTENT" ]; then
        printf "New env content detected. Updating secret...\n"
        for VERSION_ID in $(gcloud secrets versions list {{ cookiecutter.project_slug.replace('_', '-') }} --filter="state != disabled" --format="value(name)" --sort-by="~createTime"); do
          gcloud secrets versions disable $VERSION_ID --secret="{{ cookiecutter.project_slug.replace('_', '-') }}"
        done
        gcloud secrets versions add {{ cookiecutter.project_slug.replace('_', '-') }} --data-file=$env_file
      else
        printf "$env_file content matches last secret version. Skipping env update...\n"
      fi
      printf "INFO: Trigger found, deploying...\n"
      gcloud beta builds triggers run {{ cookiecutter.project_slug.replace('_', '-') }} \
        --project="$GCLOUD_PROJECT_ID" \
        --region="{{cookiecutter.gcloud_region}}" \
        --branch="main" > /dev/null && echo "Cloud Build trigger has been run: see at https://console.cloud.google.com/cloud-build/builds;region={{cookiecutter.gcloud_region}}?authuser=0&project="$GCLOUD_PROJECT_ID"&supportedpurview=project"
  else
    # Add required API activation
    printf "INFO: Checking and enabling required APIs...\n"
    gcloud services enable \
        secretmanager.googleapis.com \
        artifactregistry.googleapis.com \
        cloudbuild.googleapis.com \
        --project $GCLOUD_PROJECT_ID

    # Create and fill required secret manager
    printf "\nINFO: Creating and filling secret manager...\n"
    gcloud secrets create {{ cookiecutter.project_slug.replace('_', '-') }} \
        --replication-policy="automatic" \
        --project="$GCLOUD_PROJECT_ID" \
        --data-file="$env_file"

    # Create required bucket for terraform state
    printf "\nINFO: Creating Terraform state bucket...\n"
    gsutil mb -c standard -l {{cookiecutter.gcloud_region}} gs://$GCLOUD_PROJECT_ID-tfstate

    # Create required artifact registry for Cloud Run image
    printf "\nINFO: Creating Artifact registry repository...\n"
    gcloud artifacts repositories create "{{ cookiecutter.project_slug.replace('_', '-') }}-repository" \
      --location=europe \
      --repository-format=docker \
      --description="Images for building {{ cookiecutter.project_slug.replace('_', '-') }} Cloud Run service"

    # Add required IAM policies for Cloud Build
    printf "\nINFO: Adding required IAM policies on Cloud Build default SA...\n"
    SERVICE_ACCOUNT_EMAIL=$(gcloud projects get-iam-policy $GCLOUD_PROJECT_ID \
      --flatten="bindings[].members" \
      --filter="bindings.role:roles/cloudbuild.builds.builder AND bindings.members:'serviceAccount:'" \
      --format='value(bindings.members)')

    gcloud projects add-iam-policy-binding $GCLOUD_PROJECT_ID \
      --member="$SERVICE_ACCOUNT_EMAIL" \
      --role="roles/run.admin" > /dev/null && echo "Role run.admin granted to $SERVICE_ACCOUNT_EMAIL"

    gcloud projects add-iam-policy-binding $GCLOUD_PROJECT_ID \
      --member="$SERVICE_ACCOUNT_EMAIL" \
      --role="roles/artifactregistry.admin" > /dev/null && echo "Role roles/artifactregistry.admin granted to $SERVICE_ACCOUNT_EMAIL"

    gcloud projects add-iam-policy-binding $GCLOUD_PROJECT_ID \
      --member="$SERVICE_ACCOUNT_EMAIL" \
      --role="roles/datastore.owner" > /dev/null && echo "Role roles/datastore.owner granted to $SERVICE_ACCOUNT_EMAIL"

    gcloud projects add-iam-policy-binding $GCLOUD_PROJECT_ID \
      --member="$SERVICE_ACCOUNT_EMAIL" \
      --role="roles/cloudsql.admin" > /dev/null && echo "Role cloudsql.admin granted to $SERVICE_ACCOUNT_EMAIL"

    gcloud projects add-iam-policy-binding $GCLOUD_PROJECT_ID \
      --member="$SERVICE_ACCOUNT_EMAIL" \
      --role="roles/secretmanager.secretAccessor" > /dev/null && echo "Role secretmanager.secretAccessor granted to $SERVICE_ACCOUNT_EMAIL"

    gcloud projects add-iam-policy-binding $GCLOUD_PROJECT_ID \
      --member="$SERVICE_ACCOUNT_EMAIL" \
      --role="roles/storage.admin" > /dev/null && echo "Role storage.admin granted to $SERVICE_ACCOUNT_EMAIL"

    gcloud projects add-iam-policy-binding $GCLOUD_PROJECT_ID \
      --member="$SERVICE_ACCOUNT_EMAIL" \
      --role="roles/serviceusage.serviceUsageAdmin" > /dev/null && echo "Role serviceusage.serviceUsageAdmin granted to $SERVICE_ACCOUNT_EMAIL"

    gcloud projects add-iam-policy-binding $GCLOUD_PROJECT_ID \
      --member="$SERVICE_ACCOUNT_EMAIL" \
      --role roles/iam.serviceAccountUser > /dev/null && echo "Role iam.serviceAccountUser granted to $SERVICE_ACCOUNT_EMAIL"
  
    # Create Cloud Build trigger (repository must be already connected)
    printf "\nINFO: Creating Cloud Build trigger...\n"
    gcloud beta builds triggers create github \
        --name="{{ cookiecutter.project_slug.replace('_', '-') }}" \
        --branch-pattern="main" \
        --build-config=".cloudbuild/cloudbuild.yaml" \
        --project="$GCLOUD_PROJECT_ID" \
        --repo-owner="$(echo "{{cookiecutter.repository_name}}" | cut -d'/' -f1)" \
        --repo-name="$(echo "{{cookiecutter.repository_name}}" | cut -d'/' -f2)" \
        --substitutions=_ENV="dev" \
        --region="{{cookiecutter.gcloud_region}}"

    # Run the trigger to deploy for the first time
    printf "\nINFO: Deploying by running trigger...\n"
    gcloud beta builds triggers run {{ cookiecutter.project_slug.replace('_', '-') }} \
        --project="$GCLOUD_PROJECT_ID" \
        --region="{{cookiecutter.gcloud_region}}" \
        --branch="main" > /dev/null && echo "Cloud Build trigger has been run: see at https://console.cloud.google.com/cloud-build/builds;region={{cookiecutter.gcloud_region}}?authuser=0&project="$GCLOUD_PROJECT_ID"&supportedpurview=project"
  fi
else
  echo "Deployment aborted."
  exit 0
fi