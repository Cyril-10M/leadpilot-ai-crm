# LeadPilot AI

AI-powered lead qualification CRM built for the Volopay Sales Squad Assessment.

## Run locally
1. Install Python 3.10+
2. `pip install -r requirements.txt`
3. `streamlit run app.py`

## Deploy
Push these files to a GitHub repository, then deploy the repository on Streamlit Community Cloud.

Note: SQLite persists locally, but some free cloud hosts may reset local storage during app redeploy/restart. For assessment-grade durable cloud persistence, connect the same app to a hosted database such as Supabase/Postgres.
