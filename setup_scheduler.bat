@echo off
echo ========================================================
echo ⏰ CONFIGURING GOOGLE CLOUD SCHEDULER JOBS (IST)
echo ========================================================

set SERVICE_URL=https://prava-pipeline-service-254602453618.asia-south1.run.app

echo [1/3] Scheduling Kissa-e-Machine Content (09:00 AM IST daily)...
call gcloud scheduler jobs create http prava-content-daily ^
  --schedule="0 9 * * *" ^
  --time-zone="Asia/Kolkata" ^
  --uri="%SERVICE_URL%/trigger/content" ^
  --http-method=POST ^
  --location=asia-south1 ^
  --attempt-deadline=300s

echo [2/3] Scheduling Targeted Lead Outreach (11:00 AM IST daily)...
call gcloud scheduler jobs create http prava-outreach-daily ^
  --schedule="0 11 * * *" ^
  --time-zone="Asia/Kolkata" ^
  --uri="%SERVICE_URL%/trigger/outreach" ^
  --http-method=POST ^
  --location=asia-south1 ^
  --attempt-deadline=300s

echo [3/3] Scheduling Evening Intelligence Briefing (09:00 PM IST daily)...
call gcloud scheduler jobs create http prava-briefing-daily ^
  --schedule="0 21 * * *" ^
  --time-zone="Asia/Kolkata" ^
  --uri="%SERVICE_URL%/trigger/briefing" ^
  --http-method=POST ^
  --location=asia-south1 ^
  --attempt-deadline=300s

echo ✅ Cloud Scheduler setup complete!
