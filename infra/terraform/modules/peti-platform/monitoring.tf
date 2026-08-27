resource "google_monitoring_dashboard" "platform" {
  dashboard_json = jsonencode({
    displayName = "PETi ${var.environment} platform"
    gridLayout = {
      columns = 2
      widgets = [
        { title = "API request rate", xyChart = { dataSets = [{ timeSeriesQuery = { timeSeriesFilter = { filter = "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${google_cloud_run_v2_service.api.name}\" metric.type=\"run.googleapis.com/request_count\"" } } }] } },
        { title = "Worker request rate", xyChart = { dataSets = [{ timeSeriesQuery = { timeSeriesFilter = { filter = "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${google_cloud_run_v2_service.worker.name}\" metric.type=\"run.googleapis.com/request_count\"" } } }] } },
        { title = "API latency", xyChart = { dataSets = [{ timeSeriesQuery = { timeSeriesFilter = { filter = "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${google_cloud_run_v2_service.api.name}\" metric.type=\"run.googleapis.com/request_latencies\"" } } }] } },
        { title = "Task queue depth", xyChart = { dataSets = [{ timeSeriesQuery = { timeSeriesFilter = { filter = "resource.type=\"cloud_tasks_queue\" resource.labels.queue_id=\"${google_cloud_tasks_queue.analysis.name}\" metric.type=\"cloudtasks.googleapis.com/queue/task_count\"" } } }] } }
      ]
    }
  })
  depends_on = [google_project_service.services]
}

resource "google_monitoring_alert_policy" "task_backlog" {
  count        = var.enable_task_backlog_alert ? 1 : 0
  display_name = "PETi ${var.environment} analysis queue backlog"
  combiner     = "OR"
  conditions {
    display_name = "Analysis tasks pending"
    condition_threshold {
      filter          = "resource.type=\"cloud_tasks_queue\" AND resource.labels.queue_id=\"${google_cloud_tasks_queue.analysis.name}\" AND metric.type=\"cloudtasks.googleapis.com/queue/task_count\""
      comparison      = "COMPARISON_GT"
      threshold_value = 100
      duration        = "600s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  documentation { content = "Investigate queue backlog, worker health, and provider availability." }
  depends_on = [google_project_service.services]
}
