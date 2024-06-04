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
from SystemCheck import SystemCheck
from UpdateFiles import UpdateFiles
from Restart import Restart
from UpdateChecker import UpdateChecker
from MonitorProc import MonitorProc



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
            level=logging.info,  # Set the logging level to DEBUG to capture all log messages
            format='%(asctime)s - %(levelname)s - %(message)s'  # Define the log message format
        )

        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Check if the options file exists and load or create it
        options_file = "options.json"

        if not os.path.exists(options_file):
            logging.warning("Unable to find options.json file.  Creating new file.")
            system_checker = SystemCheck()
            system_checker.check_options()  # This will create the file if not present

        with open(options_file, 'r') as file:
            logging.info("Reading options.json file.")
            myglobals.options = json.load(file)
            logging.info("Option validation in progress")
            validation = OptionsValidator(myglobals.options)
            validation_errors = validation.validate()
            if validation_errors:
                for error in validation_errors:
                    logging.error(error)
                return  # Exit if there are validation errors
            logging.info("Options loaded and validated")

        # Initialize system checks
        system_checker = SystemCheck()
        logging.info("Verifying system integrity")
        system_checker.check_options()

        if myglobals.options.get("AutoUpdate", False):

            updater = UpdateFiles()
            logging.info("Checking for latest mining software")
            myglobals.updates_available = updater.check_for_updates()

            if myglobals.updates_available:

                logging.info("New mining software available. Download in progress")

                updated = updater.download_and_replace()

                # Perform benchmarking if required
                logging.info("Looking for benchmark file")
                benchmark_file_path = os.path.join(myglobals.options.get('FilePath', os.getcwd()), 'benchmarks.txt')
                should_benchmark = myglobals.options.get("AutoBench", False) and (
                        not os.path.exists(benchmark_file_path) or updated)

                if should_benchmark:
                    logging.info("Benchmarks unavailable.  Running benchmarks")
                    benchmark = Benchmark()
                    benchmark.perform_benchmark()

        # Initialize and start processes for the first time
        process_starter = StartProcess()
        logging.info("Starting up the miners")
        start_processes(process_starter)

        #Start the update thread
        myglobals.update_event.clear()
        restarter = Restart()
        logging.info("Beginning to check for updates regularly")
        update_checker = UpdateChecker(restarter)
        myglobals.update_thread = threading.Thread(target=update_checker.check_updates_periodically, args=(), daemon=True)
        myglobals.update_thread.start()

        if myglobals.options.get('CPUMining'):
            cpu_monitor = MonitorProc('CPUProcess', 'CPUMonitor')
            logging.info("Monitoring CPU miner")
            cpu_monitor.start()


        if myglobals.options.get('GPUMining'):
            gpu_monitor = MonitorProc('GPUProcess', 'GPUMonitor')
            logging.info("Monitoring GPU miner")
            gpu_monitor.start()


        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)


def main():
    startup_program = StartupProgram()
    logging.info("Initializing")
    startup_program.startup_program()


if __name__ == "__main__":
    main()
