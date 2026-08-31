module "peti" {
  source                = "../../modules/peti-platform"
  project_id            = var.project_id
  region                = var.region
  environment           = "judge"
  api_image             = var.api_image
  worker_image          = var.worker_image
  ai_provider           = "GEMINI"
  ai_enabled            = true
  ai_provider_enabled   = true
  ai_model_enabled      = true
  agent_runtime_enabled = true
  lab_enabled           = true
  lab_telemetry_enabled = true
  lab_feedback_enabled  = true
  lab_admin_enabled     = true
}

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "europe-west1"
}
variable "api_image" { type = string }
variable "worker_image" { type = string }
output "api_url" { value = module.peti.api_url }
output "worker_url" { value = module.peti.worker_url }
