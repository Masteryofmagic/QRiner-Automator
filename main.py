import logging
import json
import os
import signal
import sys

from SystemCheck import SystemCheck
from StartProcess import StartProcess
from MonitorProc import ProcessMonitor
from UpdateFiles import UpdateFiles
from Benchmark import Benchmark
from OptionsValidator import OptionsValidator

# Global variable to hold process monitors
process_monitors = []


def signal_handler(signal_received, frame):
    logging.info('SIGINT or CTRL-C detected. Exiting gracefully.')
    for monitor in process_monitors:
        monitor.terminate_process()
    sys.exit(0)


def main():
    global process_monitors

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Check if the options file exists and load or create it
    options_file = "options.json"
    if not os.path.exists(options_file):
        logging.warning("Options file not found. Stand by while options are created")
        system_checker = SystemCheck()
        system_checker.check_options()
    with open(options_file, 'r') as file:
        options = json.load(file)

    validation = OptionsValidator(options)
    validation_errors = validation.validate()
    if validation_errors:
        for error in validation_errors:
            logging.error(error)
        return  # Exit if there are validation errors

    logging.info("Options loaded and validated")

    # Repository configurations
    repos = {
        'CPUMining': {'owner': 'Qubic-Solutions', 'repo': 'rqiner-builds'},
        'GPUMining': {'owner': 'Qubic-Solutions', 'repo': 'rqiner-gpu-builds'}
    }

    # Initialize system checks
    system_checker = SystemCheck()
    system_checker.check_options()

    # Step 2: Initialize and run updates if AutoUpdate is enabled
    updater = UpdateFiles(options, options.get('FilePath', './downloads'), repos)
    updated = updater.check_for_updates()

    # Benchmarking process
    benchmark_file_path = os.path.join(options.get('FilePath', os.getcwd()), 'benchmarks.txt')
    should_benchmark = options.get("AutoBench", False) and (not os.path.exists(benchmark_file_path) or updated)
    if should_benchmark:
        logging.info("Benchmarking conditions met. Proceeding with benchmark.")
        benchmark = Benchmark(options.get('FilePath', os.getcwd()), options.get('ThreadCount', os.cpu_count()))
        benchmark.perform_benchmark()

    # Start and monitor processes
    process_starter = StartProcess(options)

    if options.get("CPUMining", False):
        cpu_process = process_starter.start("CPU")
        if cpu_process:
            cpu_monitor = ProcessMonitor(cpu_process, options)
            process_monitors.append(cpu_monitor)
        else:
            logging.error("Failed to start CPU process.")

    if options.get("GPUMining", False):
        gpu_process = process_starter.start("GPU")
        if gpu_process:
            gpu_monitor = ProcessMonitor(gpu_process, options)
            process_monitors.append(gpu_monitor)
        else:
            logging.error("Failed to start GPU process.")

    # Start monitoring threads
    for monitor in process_monitors:
        if monitor:
            monitor.get_thread().start()


if __name__ == "__main__":
    main()
