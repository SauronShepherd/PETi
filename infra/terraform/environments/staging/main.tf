module "peti" {
  source       = "../../modules/peti-platform"
  project_id   = var.project_id
  region       = var.region
  environment  = "staging"
  api_image    = var.api_image
  worker_image = var.worker_image
  billing_account_id = var.billing_account_id
  budget_amount = var.budget_amount
  google_oauth_client_id = var.google_oauth_client_id
  google_oauth_client_secret = var.google_oauth_client_secret
}

variable "project_id" { type = string }
variable "region" { type = string, default = "europe-west1" }
variable "api_image" { type = string }
variable "worker_image" { type = string }
variable "billing_account_id" { type = string, default = null }
variable "budget_amount" { type = number, default = 250 }
variable "google_oauth_client_id" { type = string, default = null }
variable "google_oauth_client_secret" { type = string, sensitive = true, default = null }

output "api_url" { value = module.peti.api_url }
output "worker_url" { value = module.peti.worker_url }
