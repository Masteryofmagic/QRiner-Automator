import subprocess
import threading
import logging
import time

class ProcessMonitor:
    def __init__(self, process, options):
        self.process = process
        self.options = options
        self.thread = None
        self.active = False
        self.unexpected_termination = False

    def monitor_process(self):
        """Monitor the existing process and manage its lifecycle based on the specified options."""
        self.active = True
        logging.info(f"Monitoring started for process: {self.process.args}")
        self._monitor_loop()

    def _monitor_loop(self):
        """ Internal monitoring loop that can be safely restarted. """
        polling_interval = 30
        last_logged_time = time.time()

        while self.active:
            result = self.process.poll()
            if result is None:
                # Process is still running
                current_time = time.time()
                if current_time - last_logged_time >= polling_interval:
                    logging.info(f"Process {self.process.args} is still running.")
                    last_logged_time = current_time
                time.sleep(1)
            else:
                # Process has terminated
                self.active = False
                if result != 0:
                    self.unexpected_termination = True
                    logging.error(f"Process terminated unexpectedly with return code {result}")
                    if self.options.get('AutoRestart', False):
                        self.restart_process()
                break

    def restart_process(self):
        """Restart the monitored process."""
        if self.process.poll() is not None:  # The process has terminated
            command = self.process.args
            self.process = subprocess.Popen(command)
            self.unexpected_termination = False
            logging.info(f"Process {self.process.args} restarted.")
            # Ensure the monitoring thread is restarted
            self.start_monitoring()

    def start_monitoring(self):
        """Start or restart the monitoring thread."""
        if self.thread is not None and self.thread.is_alive():
            self.active = False  # Request the existing thread to stop
            self.thread.join()  # Wait for the thread to finish
        self.active = True
        self.thread = threading.Thread(target=self.monitor_process, daemon=True)
        self.thread.start()

    def terminate_process(self):
        """Terminate the associated process and monitoring thread."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            logging.info(f"Process {self.process.args} terminated.")
        self.active = False  # Stop the monitoring loop

    def get_thread(self):
        return self.thread

    def is_active(self):
        return self.active and self.thread.is_alive()

    def has_terminated_unexpectedly(self):
        return self.unexpected_termination
