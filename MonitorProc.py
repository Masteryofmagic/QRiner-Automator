import os
import signal
import subprocess
import threading
import logging
import time

class ProcessMonitor:
    def __init__(self, process, options, restart_callback, process_starter, process_monitors, process_threads):
        self.process = process
        self.options = options
        self.restart_callback = restart_callback
        self.process_starter = process_starter
        self.process_monitors = process_monitors
        self.process_threads = process_threads
        self.active = False
        self.unexpected_termination = False
        self.thread = None
        self.label_value = self.get_label_value()
        self.lock = threading.Lock()
        logging.info(f"ProcessMonitor initialized for process: {self.get_label_value()}")

    logging.basicConfig(
        level=logging.DEBUG,  # Set the logging level to DEBUG to capture all log messages
        format='%(asctime)s - %(levelname)s - %(message)s'  # Define the log message format
    )
    def get_label_value(self):
        args = self.process.args
        if isinstance(args, str):
            args = args.split()

        if '--label' in args:
            label_index = args.index('--label')
            if label_index + 1 < len(args):
                return args[label_index + 1]
        return None

    def monitor_process(self, polling_interval=300):
        logging.info(f"Entered monitor_process for process: {self.get_label_value()}")
        self.set_active(True)
        last_logged_time = time.time()

        try:
            while self.is_active():
                # Add detailed logging before polling
                logging.debug(f"Polling the process: {self.get_label_value()}")
                raw_poll_result = self.process.poll()
                logging.debug(f"Raw poll result: {raw_poll_result}")

                result = self.process.poll()
                logging.debug(f"Assigned poll result: {result}")

                if result is None:
                    current_time = time.time()
                    if current_time - last_logged_time >= polling_interval:
                        logging.info(f"Process {self.get_label_value()} is still running.")
                        last_logged_time = current_time
                    time.sleep(1)
                else:
                    self.set_active(False)
                    if result != 0:
                        self.set_unexpected_termination(True)
                        logging.error(f"Process terminated unexpectedly with exit code {result}")
                        if self.options.get('AutoRestart', False):
                            self.restart_callback(self.options, self.process_starter, self.process_monitors, self.process_threads)
                    else:
                        logging.info(f"Process {self.get_label_value()} terminated successfully with exit code {result}")
                    break
        except Exception as e:
            logging.error(f"Error occurred in monitor_process: {str(e)}")
        finally:
            logging.info(f"Monitoring stopped for process: {self.get_label_value()}")

    def start_monitoring(self, polling_interval=300):
        if self.thread and self.thread.is_alive():
            self.set_active(False)
            self.thread.join()
        self.thread = threading.Thread(target=self.monitor_process, args=(polling_interval,), daemon=True)
        logging.info(f"New monitoring thread created for process: {self.get_label_value()}")
        self.thread.start()

    def terminate_process(self):
        if self.process and self.process.poll() is None:
            try:
                if os.name == 'nt':  # Windows
                    self.process.terminate()
                else:  # Unix-like systems
                    self.process.send_signal(signal.SIGTERM)
                self.process.wait(timeout=10)  # Wait for process to terminate gracefully
            except subprocess.TimeoutExpired:
                logging.warning(f"Process {self.get_label_value()} did not terminate gracefully. Force killing.")
                self.process.kill()
            logging.info(f"Process {self.get_label_value()} terminated.")
        self.set_active(False)

    def get_thread(self):
        if self.thread is None:
            logging.error("get_thread called, but self.thread is None")
        return self.thread

    def is_active(self):
        with self.lock:
            return self.active and self.thread.is_alive()

    def set_active(self, value):
        with self.lock:
            self.active = value

    def has_terminated_unexpectedly(self):
        with self.lock:
            return self.unexpected_termination

    def set_unexpected_termination(self, value):
        with self.lock:
            self.unexpected_termination = value
