import os
import logging
from datetime import datetime
import requests

class UpdateFiles:
    def __init__(self, options, download_path, repos):
        self.options = options
        self.download_path = download_path
        self.repos = repos
        os.makedirs(self.download_path, exist_ok=True)  # Ensure the download path exists

    def check_for_updates(self):
        """Initiates the update process based on configuration."""
        if self.options.get("CPUMining", False):
            self.check_and_update('CPUMining')
        if self.options.get("GPUMining", False):
            self.check_and_update('GPUMining')

    def check_and_update(self, mining_type):
        """Checks and updates files based on mining type."""
        repo_info = self.repos.get(mining_type)
        if not repo_info:
            logging.error(f"No repository information found for {mining_type}")
            return
        logging.info(f"Checking for updates for {mining_type}...")
        if self.download_and_replace(mining_type, repo_info):
            logging.info(f"Updates for {mining_type} completed successfully.")
        else:
            logging.info(f"No updates necessary or updates failed for {mining_type}.")

    def download_and_replace(self, mining_type, repo_info):
        """Downloads and updates the local file if it's outdated."""
        updates_made = False
        logging.info(f"Updating for {mining_type}")
        assets = self.get_latest_release_info(repo_info['owner'], repo_info['repo'])
        for name, url, upload_date in assets:
            local_file_path = os.path.join(self.download_path, name)
            if not os.path.exists(local_file_path) or self.is_local_file_older(local_file_path, upload_date):
                if self.download_file(url, local_file_path):
                    updates_made = True
        return updates_made

    def get_latest_release_info(self, repo_owner, repo_name):
        """Fetches the latest release information from a specified GitHub repository."""
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            release_info = response.json()
            return [(asset['name'], asset['browser_download_url'], asset['updated_at'])
                    for asset in release_info['assets'] if 'exe' in asset['name']]
        else:
            logging.error(f"Failed to fetch the latest release info for {repo_name}. Status code: {response.status_code}")
            return []

    def download_file(self, url, local_file_path):
        """Handles the downloading of files from URL to a local path."""
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_file_path, 'wb') as file:
                file.write(response.content)
            logging.info(f"Downloaded and updated: {os.path.basename(local_file_path)}")
            return True
        else:
            logging.error(f"Failed to download {os.path.basename(local_file_path)}. Status code: {response.status_code}")
            return False

    def is_local_file_older(self, local_file_path, github_upload_date_str):
        """Compares the local file modification date to the GitHub file upload date."""
        try:
            if not os.path.exists(local_file_path):
                return True  # File is "older" if it doesn't exist
            local_mod_date = datetime.fromtimestamp(os.path.getmtime(local_file_path))
            github_upload_date = datetime.strptime(github_upload_date_str, "%Y-%m-%dT%H:%M:%SZ")
            return local_mod_date < github_upload_date
        except Exception as err:
            logging.error(f"Error checking file dates for {local_file_path}: {err}")
            return False

# Setup logging to output to console at the debug level
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
