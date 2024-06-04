import logging
import myglobals

from UpdateFiles import UpdateFiles

class UpdateChecker:

    def __init__(self,restarter):
        self.restarter = restarter
    def check_updates_periodically(self):
        while not myglobals.update_event.is_set():
            if myglobals.options.get("AutoUpdate", False):
                logging.info("AutoUpdate is enabled. Checking for updates...")
                updater = UpdateFiles()

                # Check for updates
                myglobals.updates_available = updater.check_for_updates()

                if myglobals.updates_available:
                    logging.info("Updates available. Restarting processes...")

                    self.restarter.terminate_all_processes()

                    if myglobals.cpu_updates_available:
                        logging.info("CPU updates available. Downloading updates...")
                        cpu_updated, _ = updater.download_and_replace()
                        if cpu_updated:
                            logging.info("CPU updates downloaded.")

                    if myglobals.gpu_updates_available:
                        logging.info("GPU updates available. Downloading updates...")
                        _, gpu_updated = updater.download_and_replace()
                        if gpu_updated:
                            logging.info("GPU updates downloaded.")

                    # Restart processes after updates
                    logging.info("Restarting processes after updates...")
                    self.restarter.restart_processes()

            myglobals.update_event.wait(300)  # Check for updates every 5 minutes
