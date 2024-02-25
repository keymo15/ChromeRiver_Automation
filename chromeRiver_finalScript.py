import os
import logging
import time
import smtplib
import pysftp
import warnings
import datetime

warnings.filterwarnings(action='ignore', module='.*paramiko.*')

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
from datetime import timedelta

# Set up logging
logging.basicConfig(filename='sftp.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

import os

FTP_SERVER = os.getenv("FTP_SERVER")
FTP_USERNAME = os.getenv("FTP_USERNAME")
FTP_PASSWORD = os.getenv("FTP_PASSWORD")
FTP_DIRECTORY = os.getenv("FTP_DIRECTORY")
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def connect_ftp():
    MAX_RETRIES = 3  # Maximum number of retries
    RETRY_DELAY = 5  # Delay between retries in seconds

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  # Disable host key checking.

    for attempt in range(MAX_RETRIES):
        try:
            logging.info("Attempting to connect to SFTP server...")
            sftp = pysftp.Connection(FTP_SERVER, username=FTP_USERNAME, password=FTP_PASSWORD, cnopts=cnopts)
            logging.info("Successfully connected to SFTP server.")
            return sftp
        except Exception as e:
            logging.error(f"SFTP error: {e}")
            if attempt < MAX_RETRIES - 1:  # If this wasn't the last attempt
                logging.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)  # Wait before retrying
            else:
                logging.error(f"Failed to connect after {MAX_RETRIES} attempts.")
    return None


def download_files(sftp):
    downloaded_files = []
    upload_dates = []
    try:
        files = sftp.listdir_attr(FTP_DIRECTORY)
        files.sort(key=lambda f: f.st_mtime, reverse=True)
        current_time = time.time()

        for file in files:
            if current_time - file.st_mtime > 172800:
                continue
            base_file = file.filename
            logging.info(f"Attempting to download file: {base_file}")

            # Save the upload date of the file
            upload_date = datetime.datetime.fromtimestamp(file.st_mtime).date()
            upload_dates.append(upload_date)

            # Create a new directory for the upload date
            new_local_directory = os.path.join(LOCAL_DIRECTORY, str(upload_date))
            os.makedirs(new_local_directory, exist_ok=True)

            # Check if file already exists in new local directory
            local_file_path = os.path.join(new_local_directory, base_file)
            try:
                if os.path.isfile(local_file_path):
                    logging.info(f"File {base_file} already exists in local directory. Skipping download.")
                    continue
            except Exception as e:
                logging.error(f"Error checking if file exists: {e}")
                continue

            # Download the file
            remote_file_path = FTP_DIRECTORY + '/' + base_file
            try:
                sftp.get(remote_file_path, local_file_path)
                logging.info(f"File {base_file} downloaded successfully.")
                downloaded_files.append(local_file_path)
            except FileNotFoundError:
                logging.error(f"File {base_file} does not exist on the server.")
            except Exception as e:
                logging.error(f"Error downloading file: {e}")
    except Exception as e:
        logging.error(f"SFTP error: {e}")

    # Get the common upload date
    common_upload_date = max(set(upload_dates), key=upload_dates.count)
    return downloaded_files, common_upload_date


def send_email(subject, body, recipients, cc_recipients=[]):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ', '.join(recipients)
    msg['Cc'] = ', '.join(cc_recipients)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Use SMTP with STARTTLS for Office 365
    server = smtplib.SMTP('smtp.office365.com', 587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL_ADDRESS, recipients + cc_recipients, text)
    server.quit()

def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

def job():
    sftp = connect_ftp()
    if sftp is not None:
        try:
            # Download files and collect paths of downloaded files and their upload date
            downloaded_files, common_upload_date = download_files(sftp)

            # Calculate the previous date
            previous_date = common_upload_date - timedelta(days=1)

            # Format the dates
            formatted_common_upload_date = custom_strftime('{S} %B', common_upload_date)
            formatted_previous_date = custom_strftime('{S} %B', previous_date)

            # Create a new directory for the upload date
            new_local_directory = os.path.join(LOCAL_DIRECTORY, str(common_upload_date))
            os.makedirs(new_local_directory, exist_ok=True)

            # Move downloaded files to the new local directory
            for file_path in downloaded_files:
                os.rename(file_path, os.path.join(new_local_directory, os.path.basename(file_path)))

            # Send email with the SharePoint link in the body
            recipients = ['user.name@email.com']
            cc_recipients = ['user.name@email.com']
            if downloaded_files:
                body = f"""Hi Everyone,

Please follow the link below for this week’s files, approved through to {formatted_previous_date}.

You can access the files here: https://companyxyz.sharepoint.com/ports?

Please review the files, make sure that both reports agree for your location, and let me know if there are any issues or if you have any questions.

Thanks



"""
            else:
                body = f"No new files were downloaded."
            subject = f"Chrome River Exports - {formatted_common_upload_date}"   
            send_email(subject, body, recipients, cc_recipients)
        except Exception as e:
            logging.error(f"Job error: {e}")
            recipients = ['user.name@email.com']
            body = f"The SFTP download job failed with the following error: {e}"
            send_email("Expense reports Download Failed", body, recipients, [])
        finally:
            sftp.close()


# Call the job function directly to download the files immediately
job()
