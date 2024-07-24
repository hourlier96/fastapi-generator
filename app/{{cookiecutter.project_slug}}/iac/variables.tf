variable "database_choosed" {
  type = object(
    {
      sql       = bool
      firestore = bool
    }
  )
  default = {
    sql       = "{{ cookiecutter.database }}" == "PostgreSQL" || "{{ cookiecutter.database }}" == "Both" ? true : false
    firestore = "{{ cookiecutter.database }}" == "Firestore" || "{{ cookiecutter.database }}" == "Both" ? true : false
  }
}

# TODO activate required apis
# variable "needed_apis" {
#   description = "List of apis needed to make the project work"
#   type        = list(string)
#   default = [
#     "compute.googleapis.com",
#     "iam.googleapis.com",
#     "sqladmin.googleapis.com",
#     "cloudfunctions.googleapis.com",
#     "storage-component.googleapis.com",
#     "dns.googleapis.com",
#     "servicenetworking.googleapis.com",
#     "certificatemanager.googleapis.com",
#     "cloudbuild.googleapis.com",
#     "sql-component.googleapis.com"
#   ]
# }
