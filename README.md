# SFTP File Downloader and Email Notifier

This Python script connects to an SFTP server, downloads files that were uploaded within the last two days, moves them to a new local directory named after the common upload date of the files, and sends an email notification with the details of the downloaded files.

## Prerequisites

- Python 3.x
- pysftp
- smtplib

## Environment Variables

The script uses the following environment variables:

- `FTP_SERVER`: The SFTP server address.
- `FTP_USERNAME`: The SFTP server username.
- `FTP_PASSWORD`: The SFTP server password.
- `FTP_DIRECTORY`: The directory on the SFTP server to download files from.
- `LOCAL_DIRECTORY`: The local directory to save the downloaded files.
- `SMTP_SERVER`: The SMTP server for sending emails.
- `SMTP_PORT`: The SMTP server port (default is 25).
- `EMAIL_ADDRESS`: The email address to send emails from.
- `EMAIL_PASSWORD`: The password for the email address.

## Usage

1. Set the environment variables.
2. Run the script: `python script_name.py`

## Logging

The script logs its progress and any errors to a file named `sftp.log`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
