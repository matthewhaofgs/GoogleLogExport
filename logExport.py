import os
import csv
import datetime
import webbrowser
from time import sleep
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Configuration ---
SCOPES = ["https://www.googleapis.com/auth/admin.reports.audit.readonly"]
TRACKING_FILE = "log_days_pulled.txt"
LOG_DIR = "workspace_logs"
CREDENTIALS_FILE = "credentials.json"
ADMIN_EMAIL_FILE = "admin_email.txt"
APPLICATION_NAMES = [
    "access_transparency", "admin", "calendar", "chat", "chrome", "context_aware_access",
    "data_studio", "drive", "gcp", "gplus", "groups", "groups_enterprise", "jamboard",
    "keep", "login", "meet", "mobile", "rules", "saml", "token", "user_accounts", "vault"
]
CSV_FIELDS = ["timestamp", "actor_email", "ip_address", "event_name", "event_type", "parameters"]

# --- Helper Functions ---

def is_first_run():
    return not (os.path.exists(CREDENTIALS_FILE) and os.path.exists(ADMIN_EMAIL_FILE))

def prompt_google_console_setup():
    print("🔧 Please ensure the following setup is complete:")
    print("1. Create a Google Cloud project:")
    webbrowser.open("https://console.cloud.google.com/projectselector2/home/dashboard")
    input("Press Enter after creating/selecting a project...")

    print("\n2. Enable the Admin SDK API:")
    webbrowser.open("https://console.cloud.google.com/apis/library/admin.googleapis.com")
    input("Press Enter after enabling the API...")

    print("\n3. Create a Service Account and download the credentials file as 'credentials.json':")
    webbrowser.open("https://console.cloud.google.com/iam-admin/serviceaccounts")
    input("Press Enter after placing 'credentials.json' in this folder...")

    print("\n4. Enable Domain-Wide Delegation:")
    webbrowser.open("https://admin.google.com/ac/owl/domainwidedelegation")
    print("Use the service account's CLIENT ID and add this scope:")
    print("   https://www.googleapis.com/auth/admin.reports.audit.readonly")
    input("Press Enter after authorizing the scopes...")

def load_tracked_days():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def mark_day_as_pulled(day):
    with open(TRACKING_FILE, "a") as f:
        f.write(f"{day}\n")

def find_next_unpulled_day():
    today = datetime.date.today()
    tracked = load_tracked_days()
    for i in range(1, 366):  # look up to 1 year back
        day = today - datetime.timedelta(days=i)
        if day.isoformat() not in tracked:
            return day
    return None

def get_monthly_log_filename(application_name, date):
    month_str = date.strftime("%Y-%m")
    return os.path.join(LOG_DIR, f"{application_name}_logs_{month_str}.csv")

def authenticate():
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError("Missing credentials.json file.")

    if not os.path.exists(ADMIN_EMAIL_FILE):
        admin_email = input("👤 Enter the super admin email address to impersonate: ").strip()
        with open(ADMIN_EMAIL_FILE, "w") as f:
            f.write(admin_email)
    else:
        with open(ADMIN_EMAIL_FILE, "r") as f:
            admin_email = f.read().strip()

    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES)
    delegated_creds = credentials.with_subject(admin_email)
    service = build("admin", "reports_v1", credentials=delegated_creds)

    # Test the credentials
    test_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    try:
        print("✅ Testing credentials with a sample query...")
        service.activities().list(
            userKey='all',
            applicationName='login',
            startTime=test_date.isoformat() + "Z",
            endTime=(test_date + datetime.timedelta(days=1)).isoformat() + "Z",
            maxResults=1
        ).execute()
        print("✅ Authentication successful!")
    except Exception as e:
        print("❌ Authentication failed. Please check your credentials and delegation.")
        print("Error:", e)
        exit(1)

    return service

def fetch_logs(service, app_name, start_time, end_time):
    all_logs = []
    page_token = None
    while True:
        try:
            response = service.activities().list(
                userKey="all",
                applicationName=app_name,
                startTime=start_time,
                endTime=end_time,
                maxResults=1000,
                pageToken=page_token
            ).execute()
            activities = response.get("items", [])
            all_logs.extend(activities)
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        except Exception as e:
            print(f"⚠️ Error fetching logs for {app_name}: {e}")
            break
    return all_logs

def flatten_log_rows(app_name, logs):
    rows = []
    for activity in logs:
        base = {
            "timestamp": activity.get("id", {}).get("time", ""),
            "actor_email": activity.get("actor", {}).get("email", ""),
            "ip_address": activity.get("ipAddress", "")
        }
        for event in activity.get("events", []):
            params = event.get("parameters", [])
            param_str = "; ".join(
                f"{p.get('name')}={p.get('value') or ','.join(p.get('multiValue', []))}"
                for p in params if p.get('name')
            )
            row = {
                **base,
                "event_name": event.get("name", ""),
                "event_type": event.get("type", ""),
                "parameters": param_str
            }
            rows.append(row)
    return rows

def write_chronological_csv(app_name, date, new_rows):
    filepath = get_monthly_log_filename(app_name, date)
    existing_rows = []

    if os.path.exists(filepath):
        with open(filepath, "r", newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            existing_rows = list(reader)

    all_rows = existing_rows + new_rows
    all_rows.sort(key=lambda r: r["timestamp"])

    with open(filepath, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

def main():
    print("🔍 Starting Google Workspace Log Export Script...")
    os.makedirs(LOG_DIR, exist_ok=True)

    if is_first_run():
        prompt_google_console_setup()

    service = authenticate()

    next_day = find_next_unpulled_day()
    if not next_day:
        print("✅ All days in the past year have already been processed.")
        return

    start_time = datetime.datetime.combine(next_day, datetime.time.min).isoformat() + "Z"
    end_time = datetime.datetime.combine(next_day + datetime.timedelta(days=1), datetime.time.min).isoformat() + "Z"

    print(f"\n📅 Fetching logs for: {next_day.isoformat()}")

    for app in APPLICATION_NAMES:
        print(f"⏳ Fetching {app} logs...")
        logs = fetch_logs(service, app, start_time, end_time)
        flat_rows = flatten_log_rows(app, logs)
        write_chronological_csv(app, next_day, flat_rows)

    mark_day_as_pulled(next_day.isoformat())
    print(f"✅ Finished processing {next_day.isoformat()}")

if __name__ == "__main__":
    main()
