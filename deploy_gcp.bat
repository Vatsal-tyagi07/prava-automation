@echo off
echo ========================================================
echo 🚀 DEPLOYING PRAVA PIPELINE TO GOOGLE CLOUD RUN (24/7)
echo Project: prava-automation-514816
echo Region:  asia-south1
echo ========================================================

echo [1/4] Setting active GCP project...
call gcloud config set project prava-automation-514816

echo [2/4] Enabling required GCP APIs...
call gcloud services enable run.googleapis.com cloudscheduler.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

echo [3/4] Building container and deploying to Cloud Run via Cloud Build...
call gcloud builds submit --config=cloudbuild.yaml .

echo [4/4] Setting up Cloud Scheduler triggers...
call setup_scheduler.bat

echo ========================================================
echo ✅ Cloud Run deployment complete!
echo ========================================================
pause
