import logging
import subprocess
import threading
import time

import myglobals
from StartProcess import StartProcess, start_processes


class RestartMonitor():
    def __init__(self, monitor_key):
        self.monitor_key = monitor_key
        self.cpu_monitor = MonitorProc("CPUProcess", monitor_key)
        self.gpu_monitor = MonitorProc("GPUProcess", monitor_key)

    def restart(self):
        if self.monitor_key == 'CPUMonitor':

           self.cpu_monitor.start()
        if self.monitor_key == 'GPUMonitor':
            self.gpu_monitor.start()


class MonitorProc:
    def __init__(self, process_key, monitor_key):
        self.process_key = process_key
        self.monitor_key = monitor_key
        self.process = myglobals.process_info.get(f'{process_key}', None)

        self.thread = None

    def start(self):


        logging.info(f"Starting monitor for: {self.monitor_key}")
        self.thread = threading.Thread(target=self.monitor)
        self.thread.start()
        myglobals.process_info[self.monitor_key] = self  # Store the monitor instance in global variables

    def monitor(self):
        while True:
            time.sleep(15)
            if self.process.poll() is not None:  # Process has exited
                logging.error(f"Process {self.process_key} has exited with return code {self.process.returncode}. Restarting...")
                myglobals.process_info[f'{self.process_key}'] = None
                self.terminate_process()
                process_starter = StartProcess()
                start_processes(process_starter)
                restart_monitor = RestartMonitor(self.monitor_key)
                restart_monitor.restart()
                break

            else:
                logging.info(f"Process {self.process_key} active.")
        #self.process.wait()


    def terminate_process(self):
        if self.process and self.process.poll() is None:
            logging.info(f"Terminating monitor process {self.process_key} with PID: {self.process.pid}")
            self.process.terminate()
            self.process.wait()
            logging.info(f"Monitor process {self.process_key} with PID: {self.process.pid} terminated.")
            self.thread = None  # Clear the thread as it's no longer valid

    def is_active(self):
        return self.process and self.process.poll() is None

    def get_thread(self):
        return self.thread
