import os
import logging
from datetime import datetime
import requests
import time
import myglobals

class UpdateFiles:
    def __init__(self):
        self.options = myglobals.options
        self.download_path = myglobals.options.get('FilePath')
        self.repos = {
            'CPUMining': myglobals.process_info['CPUMining'],
            'GPUMining': myglobals.process_info['GPUMining']
        }
        os.makedirs(self.download_path, exist_ok=True)  # Ensure the download path exists

    def check_for_updates(self):

        myglobals.updates_available = False
        myglobals.cpu_updates_available = False
        myglobals.gpu_updates_available = False
        for repo_key, repo_info in self.repos.items():

            if self.options.get(repo_key, False):  # Check if updates are enabled for this key
                logging.info(f"Checking for updates")
                if self.are_updates_available(repo_info):

                    if repo_key == 'CPUMining':
                        myglobals.cpu_updates_available = True
                        logging.info(f"Updates available for CPU miner")
                    if repo_key == 'GPUMining':
                        myglobals.gpu_updates_available = True
                        logging.info(f"Updates available for GPU miner")

        if myglobals.cpu_updates_available or myglobals.gpu_updates_available:
            return True
    def are_updates_available(self, repo_info):
        assets = self.get_latest_release_info(repo_info['owner'], repo_info['repo'])
        logging.debug(f"Assets found: {assets}")
        for name, url, upload_date in assets:
            local_file_path = os.path.join(self.download_path, name)
            if not os.path.exists(local_file_path) or self.is_local_file_older(local_file_path, upload_date):
                logging.info(f"Update needed for {name}")
                return True
        return False

    def download_and_replace(self):
        cpu_updated = False
        gpu_updated = False
        for repo_key, repo_info in self.repos.items():
            if self.options.get(repo_key, False):
                logging.debug(f"Downloading {repo_key}")
                assets = self.get_latest_release_info(repo_info['owner'], repo_info['repo'])
                for name, url, upload_date in assets:
                    local_file_path = os.path.join(self.download_path, name)
                    if not os.path.exists(local_file_path) or self.is_local_file_older(local_file_path, upload_date):
                        if self.download_file(url, local_file_path):
                            logging.debug(f"Downloaded {name} to {local_file_path}")
                            if 'cuda' in name:
                                gpu_updated = True
                            else:
                                cpu_updated = True
        return cpu_updated, gpu_updated

    def get_latest_release_info(self, repo_owner, repo_name):
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            release_info = response.json()
            logging.debug(f"Release info: {release_info}")
            return [(asset['name'], asset['browser_download_url'], asset['updated_at'])
                    for asset in release_info['assets'] if 'exe' in asset['name']]
        else:
            logging.error(f"Failed to fetch the latest release info. Status code: {response.status_code}")
            return []

    def download_file(self, url, local_file_path):
        logging.info(f"Downloading from {url}")
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
        try:
            if not os.path.exists(local_file_path):
                return True  # File is "older" if it doesn't exist
            local_mod_date = datetime.fromtimestamp(os.path.getmtime(local_file_path))
            github_upload_date = datetime.strptime(github_upload_date_str, "%Y-%m-%dT%H:%M:%SZ")
            logging.debug(f"Comparing dates for {local_file_path}: local_mod_date = {local_mod_date}, github_upload_date = {github_upload_date}")
            return local_mod_date < github_upload_date
        except Exception as err:
            logging.error(f"Error checking file dates for {local_file_path}: {err}")
            return False


