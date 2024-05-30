import logging
import os
import threading

import psutil

import myglobals
from Benchmark import Benchmark
from StartProcess import start_processes, StartProcess
from UpdateChecker import UpdateChecker
from UpdateFiles import UpdateFiles


class Restart:
    def find_and_terminate_process(self, process_name):
        logging.info(f"Scanning for process named '{process_name}' to terminate.")
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['name'] == process_name or (proc.info['exe'] and process_name in proc.info['exe']):
                    logging.info(f"Found process {proc.info['name']} with PID {proc.info['pid']}. Terminating...")
                    proc.terminate()
                    proc.wait(timeout=10)  # Wait for the process to terminate
                    logging.info(f"Process {proc.info['name']} with PID {proc.info['pid']} terminated.")
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        logging.info(f"No active process named '{process_name}' found.")

    def terminate_all_processes(self):
        logging.info("Terminating all processes and monitors...")

        process_monitors = []
        if myglobals.process_info['CPUMonitor'] is not None:
            process_monitors.append(myglobals.process_info['CPUMonitor'])
        if myglobals.process_info['GPUMonitor'] is not None:
            process_monitors.append(myglobals.process_info['GPUMonitor'])

        process_procs = []
        if myglobals.process_info['CPUProcess'] is not None:
            process_procs.append(myglobals.process_info['CPUProcess'])
        if myglobals.process_info['GPUProcess'] is not None:
            process_procs.append(myglobals.process_info['GPUProcess'])

        # Terminate monitor processes
        for monitor in process_monitors:
            monitor.terminate_process()

        if myglobals.update_thread and myglobals.update_thread.is_alive():
            if threading.current_thread() != myglobals.update_thread:
                logging.info("Stopping update thread...")
                myglobals.update_event.set()
                myglobals.update_thread.join()

        # Terminate processes in process_procs
        for proc in process_procs:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=10)
                    logging.info(f"Process {proc.args} terminated.")
            except Exception as e:
                logging.error(f"Failed to terminate process {proc.args}: {e}")

        specific_process_names = [os.path.basename(proc.args[0]) for proc in process_procs if proc.args]

        # Terminate specific processes by name
        for process_name in specific_process_names:
            self.find_and_terminate_process(process_name)

        process_monitors.clear()
        process_procs.clear()

    def restart_processes(self):
        logging.info("Restarting all processes due to updates...")

        self.terminate_all_processes()

        # Perform updates
        updater = UpdateFiles()
        cpu_updated, gpu_updated = updater.download_and_replace()

        should_benchmark = myglobals.options.get("AutoBench", False) and cpu_updated
        if should_benchmark:
            logging.info("Benchmarking conditions met. Proceeding with benchmark.")
            benchmark = Benchmark()
            benchmark.perform_benchmark()

        # Restart processes
        process_starter = StartProcess()
        start_processes(process_starter)


        myglobals.update_event.clear()
        update_checker = UpdateChecker()
        myglobals.update_thread = threading.Thread(target=update_checker.check_updates_periodically(), args=(), daemon=True)
        myglobals.update_thread.start()
