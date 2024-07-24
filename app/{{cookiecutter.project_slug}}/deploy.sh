
# Create and fill required secret manager
gcloud secrets create {{ cookiecutter.project_slug.replace('_', '-') }} \
    --replication-policy="automatic" \
    --project="{{cookiecutter.gcloud_project}}" \
    --data-file=".env.dev"

# Create required bucket for terraform state
gsutil mb -c standard -l {{cookiecutter.gcloud_region}} gs://{{cookiecutter.gcloud_project}}-tfstate

# Create required artifact registry for Cloud Run image
gcloud artifacts repositories create "{{ cookiecutter.project_slug.replace('_', '-') }}-repository" \
  --location=europe \
  --repository-format=docker \
  --description="Images for building {{ cookiecutter.project_slug.replace('_', '-') }} Cloud Run service"

SERVICE_ACCOUNT_EMAIL=$(gcloud projects get-iam-policy {{cookiecutter.gcloud_project}} \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/cloudbuild.builds.builder AND bindings.members:'serviceAccount:'" \
  --format='value(bindings.members)')

# Add required IAM policies for Cloud Build
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
gcloud beta builds triggers run {{ cookiecutter.project_slug.replace('_', '-') }} \
    --project="{{cookiecutter.gcloud_project}}" \
    --region="{{cookiecutter.gcloud_region}}" \
    --branch="main" > /dev/null && echo "Cloud Build trigger has been run"