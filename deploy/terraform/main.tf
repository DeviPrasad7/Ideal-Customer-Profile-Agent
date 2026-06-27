terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region to deploy to"
  type        = string
  default     = "us-central1"
}

variable "database_url" {
  description = "The PostgreSQL database URL (e.g. Supabase, Neon, Cloud SQL)"
  type        = string
}

variable "llm_api_key" {
  description = "API Key for the LLM provider"
  type        = string
  sensitive   = true
}

resource "google_cloud_run_service" "icp_agent_api" {
  name     = "icp-agent-api"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/icp-agent-api:latest"
        
        env {
          name  = "APP_ENV"
          value = "production"
        }
        env {
          name  = "WORKERS"
          value = "1"
        }
        env {
          name  = "DATABASE_URL"
          value = var.database_url
        }
        env {
          name  = "LLM_API_KEY"
          value = var.llm_api_key
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.icp_agent_api.name
  location = google_cloud_run_service.icp_agent_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "url" {
  value = google_cloud_run_service.icp_agent_api.status[0].url
}
