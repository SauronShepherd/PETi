module "peti" {
  source                     = "../../modules/peti-platform"
  project_id                 = var.project_id
  region                     = var.region
  environment                = "production"
  api_image                  = var.api_image
  worker_image               = var.worker_image
  billing_account_id         = var.billing_account_id
  budget_amount              = var.budget_amount
  google_oauth_client_id     = var.google_oauth_client_id
  google_oauth_client_secret = var.google_oauth_client_secret
  ai_provider                = var.ai_provider
  ai_enabled                 = var.ai_enabled
  ai_provider_enabled        = var.ai_provider_enabled
  ai_model_enabled           = var.ai_model_enabled
}

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "europe-west1"
}
variable "api_image" { type = string }
variable "worker_image" { type = string }
variable "billing_account_id" {
  type    = string
  default = null
}
variable "budget_amount" {
  type    = number
  default = 1000
}
variable "google_oauth_client_id" {
  type    = string
  default = null
}
variable "google_oauth_client_secret" {
  type      = string
  sensitive = true
  default   = null
}
variable "ai_provider" {
  type    = string
  default = "GEMINI"
}
variable "ai_enabled" {
  type    = bool
  default = true
}
variable "ai_provider_enabled" {
  type    = bool
  default = true
}
variable "ai_model_enabled" {
  type    = bool
  default = true
}

output "api_url" { value = module.peti.api_url }
output "worker_url" { value = module.peti.worker_url }
