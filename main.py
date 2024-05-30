import json
import logging
import os
import signal
import sys
import threading
import time

import myglobals
from Benchmark import Benchmark
from OptionsValidator import OptionsValidator
from StartProcess import StartProcess, start_processes
from SystemCheck import SystemCheck, UpdateChecker
from UpdateFiles import UpdateFiles
from Restart import Restart



class StartupProgram:
    def __init__(self):
        pass


    def signal_handler(self, signal_received, frame):
        logging.info('SIGINT or CTRL-C detected. Exiting gracefully.')
        myglobals.update_event.set()
        if myglobals.update_thread:
            myglobals.update_thread.join()
        sys.exit(0)

    def startup_program(self):
        logging.basicConfig(
            level=logging.DEBUG,  # Set the logging level to DEBUG to capture all log messages
            format='%(asctime)s - %(levelname)s - %(message)s'  # Define the log message format
        )

        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Check if the options file exists and load or create it
        options_file = "options.json"

        if not os.path.exists(options_file):
            logging.warning("Options file not found. Stand by while options are created.")
            system_checker = SystemCheck()
            system_checker.check_options()  # This will create the file if not present

        with open(options_file, 'r') as file:
            myglobals.options = json.load(file)
            validation = OptionsValidator(myglobals.options)
            validation_errors = validation.validate()
            if validation_errors:
                for error in validation_errors:
                    logging.error(error)
                return  # Exit if there are validation errors
            logging.info("Options loaded and validated")

        # Initialize system checks
        system_checker = SystemCheck()
        system_checker.check_options()

        if myglobals.options.get("AutoUpdate", False):

            updater = UpdateFiles()

            myglobals.updates_available = updater.check_for_updates()

            if myglobals.updates_available:

                logging.info("Updates available. Downloading updates...")

                updated = updater.download_and_replace()

                # Perform benchmarking if required
                benchmark_file_path = os.path.join(myglobals.options.get('FilePath', os.getcwd()), 'benchmarks.txt')
                should_benchmark = myglobals.options.get("AutoBench", False) and (
                        not os.path.exists(benchmark_file_path) or updated)
                if should_benchmark:
                    logging.info("Benchmarking conditions met. Proceeding with benchmark.")
                    benchmark = Benchmark()
                    benchmark.perform_benchmark()

        # Initialize and start processes for the first time
        process_starter = StartProcess()
        start_processes(process_starter)

        #Start the update thread
        myglobals.update_event.clear()
        update_checker = UpdateChecker()
        myglobals.update_thread = threading.Thread(target=update_checker.check_updates_periodically, args=(), daemon=True)
        myglobals.update_thread.start()

        # Optionally wait for all monitoring threads to finish (e.g., for a clean shutdown)
        # for monitor in process_monitors:
        #     if monitor.is_active():
        #         monitor.get_thread().join()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)


def main():
    startup_program = StartupProgram()
    startup_program.startup_program()


if __name__ == "__main__":
    main()
