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

variable "needed_apis" {
  description = "List of APIs needed"
  type        = list(string)
  default = [
    "compute.googleapis.com", # Needed for network access
    "iam.googleapis.com",     # Needed for managing permissions
    "run.googleapis.com",     # Cloud Run API
  ]
}

# Local variable to dynamically build the final list of APIs
locals {
  all_needed_apis = distinct(concat(
    var.needed_apis,
    var.database_choosed.sql ? ["sqladmin.googleapis.com"] : [],
    var.database_choosed.firestore ? ["firestore.googleapis.com"] : []
  ))
}
