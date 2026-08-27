terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }
variable "api_image" { type = string }
variable "worker_image" { type = string }
variable "gemini_secret_id" {
  type    = string
  default = "peti-gemini-api-key"
}
variable "billing_account_id" {
  type    = string
  default = null
}
variable "budget_amount" {
  type    = number
  default = 100
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
  default = "FAKE"
}
variable "ai_enabled" {
  type    = bool
  default = false
}
variable "ai_provider_enabled" {
  type    = bool
  default = false
}
variable "ai_model_enabled" {
  type    = bool
  default = false
}
variable "rtdn_endpoint_url" {
  type    = string
  default = null
}
variable "rtdn_push_service_account" {
  type    = string
  default = null
}
variable "maintenance_schedule" {
  type    = string
  default = "0 * * * *"
}
variable "maintenance_time_zone" {
  type    = string
  default = "Etc/UTC"
}
variable "worker_deletion_protection" {
  type    = bool
  default = true
}
variable "enable_task_backlog_alert" {
  type    = bool
  default = true
}
variable "deployment_revision" {
  type    = string
  default = "managed"
}
variable "maintenance_task_audience" {
  type    = string
  default = null
}

locals {
  # GCP resource identifiers are lowercase; keep the public environment
  # value unchanged for configuration/display, but normalize all names.
  environment_slug     = lower(var.environment)
  maintenance_audience = "peti-maintenance-${lower(var.environment)}"
}

provider "google" {
  project               = var.project_id
  region                = var.region
  user_project_override = true
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com", "firestore.googleapis.com", "storage.googleapis.com",
    "cloudtasks.googleapis.com", "secretmanager.googleapis.com", "logging.googleapis.com",
    "monitoring.googleapis.com", "artifactregistry.googleapis.com", "iamcredentials.googleapis.com",
    "identitytoolkit.googleapis.com", "firebase.googleapis.com", "billingbudgets.googleapis.com"
    , "pubsub.googleapis.com", "cloudscheduler.googleapis.com"
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_service_account" "api" {
  account_id   = "peti-api-${local.environment_slug}"
  display_name = "PETi ${var.environment} API runtime"
}

resource "google_service_account" "worker" {
  account_id   = "peti-worker-${local.environment_slug}"
  display_name = "PETi ${var.environment} private worker runtime"
}

resource "google_pubsub_topic" "google_play_rtdn" {
  name = "peti-google-play-rtdn-${local.environment_slug}"
}

resource "google_pubsub_topic_iam_member" "google_play_rtdn_publisher" {
  topic  = google_pubsub_topic.google_play_rtdn.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_subscription" "google_play_rtdn_push" {
  name                 = "peti-google-play-rtdn-push-${local.environment_slug}"
  topic                = google_pubsub_topic.google_play_rtdn.id
  ack_deadline_seconds = 30
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "300s"
  }
  expiration_policy {
    ttl = "2592000s"
  }
  dynamic "push_config" {
    for_each = var.rtdn_endpoint_url == null ? [] : [var.rtdn_endpoint_url]
    content {
      push_endpoint = push_config.value
      oidc_token {
        service_account_email = coalesce(var.rtdn_push_service_account, google_service_account.api.email)
        audience              = push_config.value
      }
    }
  }
}

resource "google_storage_bucket" "media" {
  name                        = "${var.project_id}-peti-media-${local.environment_slug}"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  versioning { enabled = true }
  lifecycle_rule {
    condition { age = 365 }
    action { type = "Delete" }
  }
  depends_on = [google_project_service.services]
}

resource "google_firestore_database" "default" {
  project          = var.project_id
  name             = "(default)"
  location_id      = var.region
  type             = "FIRESTORE_NATIVE"
  concurrency_mode = "OPTIMISTIC"
  depends_on       = [google_project_service.services]
}

resource "google_cloud_tasks_queue" "analysis" {
  name     = "analysis-${local.environment_slug}"
  location = var.region
  rate_limits {
    max_concurrent_dispatches = 10
    max_dispatches_per_second = 2
  }
  retry_config {
    max_attempts       = 5
    max_retry_duration = "3600s"
    max_backoff        = "300s"
  }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret" "gemini" {
  secret_id = var.gemini_secret_id
  replication {
    auto {}
  }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_iam_member" "worker_gemini" {
  secret_id = google_secret_manager_secret.gemini.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_identity_platform_config" "auth" {
  project = var.project_id
  sign_in {
    allow_duplicate_emails = false
    email { enabled = false }
  }
  depends_on = [google_project_service.services]
}

resource "google_identity_platform_oauth_idp_config" "google" {
  count         = var.google_oauth_client_id == null || var.google_oauth_client_secret == null ? 0 : 1
  project       = var.project_id
  name          = "google.com"
  display_name  = "Google"
  client_id     = var.google_oauth_client_id
  client_secret = var.google_oauth_client_secret
  issuer        = "https://accounts.google.com"
  depends_on    = [google_identity_platform_config.auth]
}

resource "google_cloud_run_v2_service" "worker" {
  name                = "peti-worker-${local.environment_slug}"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  deletion_protection = var.worker_deletion_protection
  template {
    service_account = google_service_account.worker.email
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
    containers {
      image = var.worker_image
      resources { limits = { cpu = "1", memory = "1Gi" } }
      env {
        name  = "PETI_ENVIRONMENT"
        value = upper(var.environment)
      }
      env {
        name  = "PETI_DEPLOYMENT_REVISION"
        value = var.deployment_revision
      }
      env {
        name  = "PETI_SERVICE"
        value = "peti-worker"
      }
      env {
        name  = "PETI_AUTH_MODE"
        value = "FIREBASE"
      }
      env {
        name  = "PETI_STORAGE_MODE"
        value = "FIRESTORE"
      }
      env {
        name  = "PETI_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PETI_FIREBASE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PETI_FIRESTORE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PETI_MEDIA_BUCKET"
        value = google_storage_bucket.media.name
      }
      env {
        name  = "PETI_TASKS_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PETI_TASKS_LOCATION"
        value = var.region
      }
      env {
        name  = "PETI_ANALYSIS_QUEUE_NAME"
        value = google_cloud_tasks_queue.analysis.name
      }
      env {
        name  = "PETI_ANALYSIS_TASK_SERVICE_ACCOUNT"
        value = google_service_account.worker.email
      }
      env {
        name  = "PETI_ANALYSIS_EXPECTED_SERVICE_ACCOUNT"
        value = google_service_account.worker.email
      }
      env {
        name  = "PETI_AI_PROVIDER"
        value = var.ai_provider
      }
      env {
        name  = "PETI_AI_ENABLED"
        value = tostring(var.ai_enabled)
      }
      env {
        name  = "PETI_AI_PROVIDER_ENABLED"
        value = tostring(var.ai_provider_enabled)
      }
      env {
        name  = "PETI_AI_MODEL_ENABLED"
        value = tostring(var.ai_model_enabled)
      }
      dynamic "env" {
        for_each = var.ai_enabled && var.ai_provider == "GEMINI" ? [true] : []
        content {
          name = "PETI_GEMINI_API_KEYS"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.gemini.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }
  depends_on = [google_project_service.services]
}

resource "google_cloud_run_v2_service" "api" {
  name     = "peti-api-${local.environment_slug}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  template {
    service_account = google_service_account.api.email
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
    containers {
      image = var.api_image
      resources { limits = { cpu = "1", memory = "1Gi" } }
      env {
        name  = "PETI_ENVIRONMENT"
        value = upper(var.environment)
      }
      env {
        name  = "PETI_DEPLOYMENT_REVISION"
        value = var.deployment_revision
      }
      env {
        name  = "PETI_AUTH_MODE"
        value = "FIREBASE"
      }
      env {
        name  = "PETI_STORAGE_MODE"
        value = "FIRESTORE"
      }
      env {
        name  = "PETI_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PETI_FIREBASE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PETI_FIRESTORE_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PETI_MEDIA_BUCKET"
        value = google_storage_bucket.media.name
      }
      env {
        name  = "PETI_TASKS_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PETI_TASKS_LOCATION"
        value = var.region
      }
      env {
        name  = "PETI_ANALYSIS_QUEUE_NAME"
        value = google_cloud_tasks_queue.analysis.name
      }
      env {
        name  = "PETI_ANALYSIS_WORKER_URL"
        value = google_cloud_run_v2_service.worker.uri
      }
      env {
        name  = "PETI_ANALYSIS_TASK_SERVICE_ACCOUNT"
        value = google_service_account.worker.email
      }
      env {
        name  = "PETI_ANALYSIS_TASK_AUDIENCE"
        value = google_cloud_run_v2_service.worker.uri
      }
      env {
        name  = "PETI_MAINTENANCE_EXPECTED_SERVICE_ACCOUNT"
        value = google_service_account.api.email
      }
      env {
        name  = "PETI_MAINTENANCE_TASK_AUDIENCE"
        value = coalesce(var.maintenance_task_audience, local.maintenance_audience)
      }
      env {
        name  = "PETI_ANALYSIS_EXPECTED_SERVICE_ACCOUNT"
        value = google_service_account.worker.email
      }
      env {
        name  = "PETI_AI_PROVIDER"
        value = var.ai_provider
      }
      env {
        name  = "PETI_AI_ENABLED"
        value = tostring(var.ai_enabled)
      }
      env {
        name  = "PETI_AI_PROVIDER_ENABLED"
        value = tostring(var.ai_provider_enabled)
      }
      env {
        name  = "PETI_AI_MODEL_ENABLED"
        value = tostring(var.ai_model_enabled)
      }
    }
  }
  depends_on = [google_project_service.services]
}

resource "google_cloud_run_service_iam_member" "worker_invoker" {
  location = google_cloud_run_v2_service.worker.location
  service  = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.api.email}"
}

resource "google_cloud_run_service_iam_member" "api_rtdn_invoker" {
  count    = var.rtdn_endpoint_url == null ? 0 : 1
  location = google_cloud_run_v2_service.api.location
  service  = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${coalesce(var.rtdn_push_service_account, google_service_account.api.email)}"
}

resource "google_cloud_scheduler_job" "media_maintenance" {
  name      = "peti-media-maintenance-${local.environment_slug}"
  schedule  = var.maintenance_schedule
  time_zone = var.maintenance_time_zone
  region    = var.region

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.api.uri}/v1/internal/tasks/media-maintenance"
    oidc_token {
      service_account_email = google_service_account.api.email
      audience              = coalesce(var.maintenance_task_audience, local.maintenance_audience)
    }
  }
  depends_on = [google_project_service.services]
}

resource "google_project_iam_member" "api_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_storage_bucket_iam_member" "worker_media_reader" {
  bucket = google_storage_bucket.media.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "api_tasks" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_worker_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_cloud_run_service_iam_member" "worker_task_invoker" {
  location = google_cloud_run_v2_service.worker.location
  service  = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_cloud_run_service_iam_member" "scheduler_api_invoker" {
  location = google_cloud_run_v2_service.api.location
  service  = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.api.email}"
}

resource "google_service_account_iam_member" "scheduler_can_mint_api_oidc" {
  service_account_id = google_service_account.api.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "api_can_mint_worker_oidc" {
  service_account_id = google_service_account.worker.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.api.email}"
}

resource "google_service_account_iam_member" "cloud_tasks_can_mint_worker_oidc" {
  service_account_id = google_service_account.worker.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloudtasks.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "api_can_use_worker_identity" {
  service_account_id = google_service_account.worker.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.api.email}"
}

resource "google_monitoring_alert_policy" "api_error_rate" {
  display_name = "PETi ${var.environment} API error rate"
  combiner     = "OR"
  conditions {
    display_name = "Cloud Run API 5xx responses"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${google_cloud_run_v2_service.api.name}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      duration        = "300s"
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  documentation { content = "Investigate PETi API failures for ${var.environment}." }
  depends_on = [google_project_service.services]
}

resource "google_billing_budget" "environment" {
  count           = var.billing_account_id == null ? 0 : 1
  billing_account = var.billing_account_id
  display_name    = "PETi ${var.environment} monthly budget"
  amount {
    specified_amount {
      currency_code = "EUR"
      units         = tostring(var.budget_amount)
    }
  }
  budget_filter { projects = ["projects/${data.google_project.project.number}"] }
  threshold_rules { threshold_percent = 0.5 }
  threshold_rules { threshold_percent = 0.8 }
  threshold_rules { threshold_percent = 1.0 }
}

data "google_project" "project" { project_id = var.project_id }

resource "google_project_iam_member" "worker_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "api_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.api.email}"
}

output "api_url" { value = google_cloud_run_v2_service.api.uri }
output "worker_url" { value = google_cloud_run_v2_service.worker.uri }
output "media_bucket" { value = google_storage_bucket.media.name }
output "analysis_queue" { value = google_cloud_tasks_queue.analysis.name }
output "api_service_account" { value = google_service_account.api.email }
output "worker_service_account" { value = google_service_account.worker.email }
