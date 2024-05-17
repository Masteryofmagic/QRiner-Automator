import logging
import os
import subprocess

class StartProcess:
    def __init__(self, options):
        self.options = options

    def start(self, process_type):
        logging.info(f"Attempting to start {process_type} process...")
        if self.options.get("Autostart", False):  # Assuming Autostart should be a boolean
            command = self.build_command(process_type)
            if command:  # Ensure command was built successfully
                proc = self.run_process(command, process_type)
                return proc
            else:
                logging.error(f"Failed to build command for {process_type}")
        else:
            logging.info("Autostart is disabled.")

    def build_command(self, process_type):
        if process_type == "CPU":
            return self.build_cpu_command()
        elif process_type == "GPU":
            return self.build_gpu_command()

    def build_cpu_command(self):
        best_exe, highest_value = self.get_best_performing_exe()
        if not best_exe:  # Benchmark file not found or no executable determined
            if self.options.get("AutoBenchmark", False):
                from Benchmark import Benchmark  # Assume Benchmark is a module you can import
                benchmark = Benchmark(self.options.get("FilePath", os.getcwd()), self.options.get("ThreadCount", os.cpu_count()))
                benchmark.perform_benchmark()
                best_exe, highest_value = self.get_best_performing_exe()

        if best_exe:
            thread_count = self.options.get("ThreadCount", 1)
            pay_id = self.options.get("PayID", "")
            cpu_alias = self.options.get("CPUAlias", "CPU")
            return [os.path.join(self.options.get("FilePath", os.getcwd()), best_exe),
                    "--threads", str(thread_count), "--id", pay_id, "--label", cpu_alias]
        return None

    def build_gpu_command(self):
        file_path = self.options.get("FilePath", os.getcwd())
        exe_files = [f for f in os.listdir(file_path) if 'cuda' in f and f.endswith('.exe')]
        gpu_exe = exe_files[0] if exe_files else None
        pay_id = self.options.get("PayID", "")
        gpu_alias = self.options.get("GPUAlias", "GPU")

        return [os.path.join(file_path, gpu_exe), "--id", pay_id, "--label", gpu_alias]

    def get_best_performing_exe(self):
        file_path = os.path.join(self.options.get("FilePath", os.getcwd()), 'benchmarks.txt')
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
        # Directly use the boolean value for HideWindows
        hide_windows = self.options.get("HideWindows", False)
        if os.name == 'nt' and hide_windows:
            # Windows specific: hide the command window
            proc = subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            proc = subprocess.Popen(command, shell=True)

        logging.info(f"{process_type} process started with command: {' '.join(command)}")
        return proc
