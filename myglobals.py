#global variable for all modules
import threading

process_info = {
    'CPUMonitor': None,
    'CPUProcess': None,
    'CPUCommand': None,
    'CPUMining': {'owner': 'Qubic-Solutions', 'repo': 'rqiner-builds'},
    'GPUMonitor': None,
    'GPUProcess': None,
    'GPUCommand': None,
    'GPUMining': {'owner': 'Qubic-Solutions', 'repo': 'rqiner-gpu-builds'}
}

options = {}
updates_available = False
update_thread = None
cpu_updates_available = False
gpu_updates_available = False
update_event = threading.Event()