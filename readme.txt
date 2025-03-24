Google Workspace Log Export Script
==================================

This script automates the export of all available Google Workspace audit logs using the Admin SDK Reports API. It downloads logs daily and stores them in local monthly CSV files, allowing retention far beyond Google's default 6-month limit.

This is ideal for compliance, auditing, internal investigations, long-term monitoring, and forensic readiness.

--------------------------------------------------------------------------------
FEATURES
--------------------------------------------------------------------------------

- Supports all known applicationName values from the Reports API
- Groups logs by month and service (e.g. drive_logs_2025-03.csv)
- Ensures logs are stored in chronological order even if pulled out of order
- Tracks which days have already been downloaded using log_days_pulled.txt
- Automatically resumes from the earliest unpulled date in the past year
- Guided first-run setup: no manual API work required
- Uses a service account with domain-wide delegation
- Designed to run on Windows
- Supports scheduled daily automation using Task Scheduler

--------------------------------------------------------------------------------
FILES AND FOLDER STRUCTURE
--------------------------------------------------------------------------------

logexport.py     The main Python script
requirements.txt                    Python packages to install
README.md                           This documentation
credentials.json                    Your service account key file (you provide)
admin_email.txt                     Stores the admin email address (auto-generated)
log_days_pulled.txt                 Tracks which days have already been processed
workspace_logs/                     Folder containing all log CSVs

Example log files inside workspace_logs:
  - drive_logs_2025-03.csv
  - login_logs_2025-03.csv
  - admin_logs_2025-03.csv

--------------------------------------------------------------------------------
PREREQUISITES
--------------------------------------------------------------------------------

- Python 3.7 or newer installed and available in system PATH
- Google Workspace account with super administrator privileges
- A Google Cloud Project with Admin SDK API enabled
- A service account with domain-wide delegation configured

--------------------------------------------------------------------------------
SETUP INSTRUCTIONS (FIRST RUN ONLY)
--------------------------------------------------------------------------------

1. Install required Python libraries:
   Open Command Prompt or PowerShell and run:

     pip install -r requirements.txt

2. Run the script:

     python logexport.py

3. Follow the on-screen prompts:
   - It will open your browser to guide you through:
     a. Creating or selecting a Google Cloud project
     b. Enabling the Admin SDK API
     c. Creating a service account and downloading the key as credentials.json
     d. Enabling domain-wide delegation
     e. Authorizing the following scope:
        https://www.googleapis.com/auth/admin.reports.audit.readonly

   - You will be asked to provide your super admin email (only once).
   - Your credentials and admin email are saved for future runs.

4. On future runs, the script will skip the setup and go straight to log export.

--------------------------------------------------------------------------------
HOW IT WORKS
--------------------------------------------------------------------------------

- On each run, the script looks back up to 1 year and finds the earliest day
  that has not yet been pulled (according to log_days_pulled.txt).

- It downloads all logs for that day from every supported applicationName.

- Logs are saved as CSV files in the workspace_logs folder, one per app per month.

- If the monthly file already exists, the script merges and sorts all entries
  chronologically before saving (to avoid duplication or disorder).

- The processed date is added to log_days_pulled.txt so it's not repeated.

- Each run processes one day at a time.

--------------------------------------------------------------------------------
SUPPORTED LOG TYPES (applicationName)
--------------------------------------------------------------------------------

The script fetches audit logs for the following applicationName values:

  access_transparency
  admin
  calendar
  chat
  chrome
  context_aware_access
  data_studio
  drive
  gcp
  gplus
  groups
  groups_enterprise
  jamboard
  keep
  login
  meet
  mobile
  rules
  saml
  token
  user_accounts
  vault

--------------------------------------------------------------------------------
AUTOMATING WITH WINDOWS TASK SCHEDULER
--------------------------------------------------------------------------------

You can configure the script to run automatically once per day using Task Scheduler:

1. Open Task Scheduler in Windows.

2. Choose "Create Basic Task" and give it a name like "Google Log Export".

3. Set the trigger to "Daily" and choose your desired time.

4. Action: "Start a program"

5. Program/script:
     C:\Path\To\python.exe

6. Add arguments:
     C:\Path\To\google_workspace_logs_export.py

7. Finish the wizard.

Make sure python.exe and the script path are correct.
You can test the task by right-clicking and selecting "Run".

--------------------------------------------------------------------------------
TROUBLESHOOTING
--------------------------------------------------------------------------------

- If authentication fails:
  - Double check your credentials.json file is present and valid
  - Make sure the service account has domain-wide delegation enabled
  - Verify the admin email has sufficient privileges

- If logs appear out of order:
  - The script automatically re-sorts monthly CSVs by timestamp every time

- If logs are missing:
  - Some logs require specific Workspace editions or feature enablement

--------------------------------------------------------------------------------
SECURITY NOTES
--------------------------------------------------------------------------------

- Treat credentials.json as a secret key. Do not expose it publicly.
- Only use this script in secure, administrator-controlled environments.
- You may choose to move logs to encrypted or offsite storage after export.

--------------------------------------------------------------------------------
RESETTING CONFIGURATION
--------------------------------------------------------------------------------

If you ever need to re-run the initial setup:

1. Delete the following files:
   - admin_email.txt
   - credentials.json (optional)

2. Run the script again.

--------------------------------------------------------------------------------
AUTHOR
--------------------------------------------------------------------------------

This script was created to help Google Workspace administrators retain audit logs
for long-term compliance and forensic readiness. You may freely modify or extend it
to suit your organization's specific needs.

--------------------------------------------------------------------------------
