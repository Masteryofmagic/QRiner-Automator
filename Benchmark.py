import os
import subprocess
import logging

class Benchmark:
    def __init__(self, file_path, thread_count):
        self.file_path = file_path
        self.thread_count = thread_count
        self.bench_array = []

    def run_command_with_timeout(self, command, timeout_sec=15):  # Fixed timeout of 15 seconds
        try:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        return stdout, stderr

    def benchmark_exes(self):
        exe_files = [f for f in os.listdir(self.file_path) if f.endswith('.exe') and 'cuda' not in f and f != 'main.exe']
        for exe_file in exe_files:
            command = f'{os.path.join(self.file_path, exe_file)} -b -t {self.thread_count}'
            stdout, stderr = self.run_command_with_timeout(command)
            stdout = stdout.decode('utf-8')
            stderr = stderr.decode('utf-8')
            logging.info(f'Output: {stderr}')

            lines = stderr.split('\n')
            last_line = lines[-2] if len(lines) >= 2 else ''
            average_index = last_line.find("Average(10): ")

            if average_index != -1:
                value = last_line[average_index + len("Average(10): "):].replace(" it/s", "")
                self.bench_array.append((exe_file, value))

            logging.info(f'Results: {stderr}')

    def save_results(self):
        with open(os.path.join(self.file_path, 'benchmarks.txt'), 'w') as file:
            for exe_file, value in self.bench_array:
                file.write(f'{exe_file}, {value}\n')

    def perform_benchmark(self):
        logging.info("Starting benchmarks...")

        self.benchmark_exes()
        self.save_results()
        logging.info("Benchmarking completed.")
