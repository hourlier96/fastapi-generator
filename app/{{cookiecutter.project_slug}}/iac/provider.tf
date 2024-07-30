terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.0.0"
    }
  }
  backend "gcs" {}
}

provider "google" {
  project = "{{ cookiecutter.gcloud_project }}"
}
