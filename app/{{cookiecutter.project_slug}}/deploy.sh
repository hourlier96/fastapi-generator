if gcloud beta builds triggers describe {{ cookiecutter.project_slug.replace('_', '-') }} \
    --project="{{cookiecutter.gcloud_project}}" \
    --region="{{cookiecutter.gcloud_region}}" &>/dev/null; then
    printf "INFO: Trigger found, deploying...\n"
    gcloud beta builds triggers run {{ cookiecutter.project_slug.replace('_', '-') }} \
      --project="{{cookiecutter.gcloud_project}}" \
      --region="{{cookiecutter.gcloud_region}}" \
      --branch="main" > /dev/null && echo "Cloud Build trigger has been run"
else
  # Add required API activation
  printf "Checking and enabling required APIs...\n"
  gcloud services enable \
      secretmanager.googleapis.com \
      artifactregistry.googleapis.com \
      cloudbuild.googleapis.com \
      --project "{{cookiecutter.gcloud_project}}"

  # Create and fill required secret manager
  printf "\nINFO: Creating and filling secret manager...\n"
  gcloud secrets create {{ cookiecutter.project_slug.replace('_', '-') }} \
      --replication-policy="automatic" \
      --project="{{cookiecutter.gcloud_project}}" \
      --data-file=".env.dev"

  # Create required bucket for terraform state
  printf "\nINFO: Creating Terraform state bucket...\n"
  gsutil mb -c standard -l {{cookiecutter.gcloud_region}} gs://{{cookiecutter.gcloud_project}}-tfstate

  # Create required artifact registry for Cloud Run image
  printf "\nINFO: Creating Artifact registry repository...\n"
  gcloud artifacts repositories create "{{ cookiecutter.project_slug.replace('_', '-') }}-repository" \
    --location=europe \
    --repository-format=docker \
    --description="Images for building {{ cookiecutter.project_slug.replace('_', '-') }} Cloud Run service"

  # Add required IAM policies for Cloud Build
  printf "\nINFO: Adding required IAM policies on Cloud Build default SA...\n"
  SERVICE_ACCOUNT_EMAIL=$(gcloud projects get-iam-policy {{cookiecutter.gcloud_project}} \
    --flatten="bindings[].members" \
    --filter="bindings.role:roles/cloudbuild.builds.builder AND bindings.members:'serviceAccount:'" \
    --format='value(bindings.members)')

  gcloud projects add-iam-policy-binding {{cookiecutter.gcloud_project}} \
    --member="$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.admin" > /dev/null && echo "Role run.admin granted to $SERVICE_ACCOUNT_EMAIL"

  gcloud projects add-iam-policy-binding {{cookiecutter.gcloud_project}} \
    --member="$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/artifactregistry.admin" > /dev/null && echo "Role roles/artifactregistry.admin granted to $SERVICE_ACCOUNT_EMAIL"

  gcloud projects add-iam-policy-binding {{cookiecutter.gcloud_project}} \
    --member="$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/datastore.owner" > /dev/null && echo "Role roles/datastore.owner granted to $SERVICE_ACCOUNT_EMAIL"

  gcloud projects add-iam-policy-binding {{cookiecutter.gcloud_project}} \
    --member="$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.admin" > /dev/null && echo "Role cloudsql.admin granted to $SERVICE_ACCOUNT_EMAIL"

  gcloud projects add-iam-policy-binding {{cookiecutter.gcloud_project}} \
    --member="$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor" > /dev/null && echo "Role secretmanager.secretAccessor granted to $SERVICE_ACCOUNT_EMAIL"

  gcloud projects add-iam-policy-binding {{cookiecutter.gcloud_project}} \
    --member="$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin" > /dev/null && echo "Role storage.admin granted to $SERVICE_ACCOUNT_EMAIL"


  # Create Cloud Build trigger (repository must be already connected)
  printf "\nINFO: Creating Cloud Build trigger...\n"
  gcloud beta builds triggers create github \
      --name="{{ cookiecutter.project_slug.replace('_', '-') }}" \
      --branch-pattern="main" \
      --build-config=".cloudbuild/cloudbuild.yaml" \
      --project="{{cookiecutter.gcloud_project}}" \
      --repo-owner="$(echo "{{cookiecutter.repository_name}}" | cut -d'/' -f1)" \
      --repo-name="$(echo "{{cookiecutter.repository_name}}" | cut -d'/' -f2)" \
      --substitutions=_ENV="dev" \
      --region="{{cookiecutter.gcloud_region}}"

  # Run the trigger to deploy for the first time
  printf "\nINFO: Deploying by running trigger...\n"
  gcloud beta builds triggers run {{ cookiecutter.project_slug.replace('_', '-') }} \
      --project="{{cookiecutter.gcloud_project}}" \
      --region="{{cookiecutter.gcloud_region}}" \
      --branch="main" > /dev/null && echo "Cloud Build trigger has been run"
fi