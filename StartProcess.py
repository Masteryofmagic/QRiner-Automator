import logging
import os
import platform
import subprocess

import myglobals
class StartProcess:
    def __init__(self):
        self.options = myglobals.options


    def start(self, process_type):
        logging.info(f"Attempting to start {process_type} process...")
        if self.options.get("Autostart", False):  # Assuming Autostart should be a boolean
            if process_type == "CPUMining" and myglobals.process_info['CPUCommand'] == None:
                command = self.build_command(process_type)
                myglobals.process_info['CPUCommand'] = command
                return self.run_process(command, process_type)
            elif process_type == "CPUMining":
                command = myglobals.process_info['CPUCommand']
                return self.run_process(command, process_type)

            if process_type == "GPUMining" and myglobals.process_info['GPUCommand'] == None:
                command = self.build_command(process_type)
                myglobals.process_info['GPUCommand'] = command
                return self.run_process(command, process_type)
            else:
                command = myglobals.process_info['GPUCommand']
                return self.run_process(command, process_type)


        else:
            logging.info("Autostart is disabled.")
        return None

    def build_command(self, process_type):
        if process_type == "CPUMining":
            return self.build_cpu_command()
        elif process_type == "GPUMining":
            return self.build_gpu_command()

    def build_cpu_command(self):
        best_exe, highest_value = self.get_best_performing_exe()
        if not best_exe:  # Benchmark file not found or no executable determined
            if myglobals.options.get("AutoBenchmark", False):
                from Benchmark import Benchmark  # Assume Benchmark is a module you can import
                benchmark = Benchmark(self.options.get("FilePath", os.getcwd()), self.options.get("ThreadCount", os.cpu_count()))
                benchmark.perform_benchmark()
                best_exe, highest_value = self.get_best_performing_exe()

        if best_exe:
            thread_count = myglobals.options.get("ThreadCount", 1)
            pay_id = myglobals.options.get("PayID", "")
            cpu_alias = myglobals.options.get("CPUAlias", "CPU")
            return [os.path.join(myglobals.options.get("FilePath", os.getcwd()), best_exe),
                    "--threads", str(thread_count), "--id", pay_id, "--label", cpu_alias]
        return None

    def build_gpu_command(self):
        file_path = myglobals.options.get("FilePath", os.getcwd())
        exe_files = [f for f in os.listdir(file_path) if 'cuda' in f and f.endswith('.exe')]
        gpu_exe = exe_files[0] if exe_files else None
        pay_id = myglobals.options.get("PayID", "")
        gpu_alias = myglobals.options.get("GPUAlias", "GPU")

        return [os.path.join(file_path, gpu_exe), "--id", pay_id, "--label", gpu_alias]

    def get_best_performing_exe(self):
        file_path = os.path.join(myglobals.options.get("FilePath", os.getcwd()), 'benchmarks.txt')
        highest_value = 0
        best_exe = None
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    parts = line.split(',')
                    if len(parts) >= 2 and float(parts[1].strip()) > highest_value:
                        highest_value = float(parts[1].strip())
                        best_exe = parts[0].strip()
        except FileNotFoundError:
            logging.warning("Benchmark file not found.")
            return None, None
        return best_exe, highest_value

    def run_process(self, command, process_type):
        hide_windows = myglobals.options.get("HideWindows", False)

        if platform.system() == 'Windows':
            if hide_windows:
                # Windows specific: run without showing the window
                proc = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Windows specific: open a new command window
                proc = subprocess.Popen(command, shell=False)

        else:
            if hide_windows:
                # Linux specific: run without showing the window
                proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Linux specific: open a new terminal window
                proc = subprocess.Popen(['xterm', '-e'] + command)

        logging.info(f"{process_type} process started with command: {' '.join(command)}")
        return proc

def start_processes(process_starter):
    if myglobals.options.get("CPUMining", False) and myglobals.process_info['CPUProcess'] == None:
        cpu_process = process_starter.start("CPUMining")
        if cpu_process:
            myglobals.process_info['CPUProcess'] = cpu_process
    if myglobals.options.get("GPUMining", False) and myglobals.process_info['GPUProcess'] == None:
        gpu_process = process_starter.start("GPUMining")
        if gpu_process:
            myglobals.process_info['GPUProcess'] = gpu_process




