import psutil
import time

def get_UMA_pid():
    result = None
    process_info = psutil.process_iter(attrs=['pid', 'name'])
    for process in process_info:
        if 'UMA' in process.info['name']:
            result = process.info['pid']
    if result is None:
        raise Exception("No UMA process found!")
    return result

class CPUMonitor:
    def __init__(self, pid):
        self._pid = pid
        self._process = psutil.Process(pid=self._pid)

    def host_cpu_times_percent(self):
        return psutil.cpu_times_percent(interval=1)

    def uma_cpu_time(self):
        return self._process.cpu_times()

    def uma_cpu_percent(self):
        return self._process.cpu_percent()

class MemMonitor:
    def __init__(self, pid):
        self._pid = pid
        self._process = psutil.Process(pid=self._pid)

    def host_mem(self):
        return psutil.virtual_memory()

    def host_swap_mem(self):
        return psutil.swap_memory()

    def uma_mem(self):
        return self._process.memory_info()

class DiskMonitor:
    def __init__(self, pid):
        self._pid = pid
        self._process = psutil.Process(pid=self._pid)

    def host_iops(self):
        return psutil.disk_io_counters()

    def uma_iops(self):
        return self._process.io_counters()

class NetworkMonitor:
    def __init__(self, pid):
        self._pid = pid
        self._process = psutil.Process(pid=self._pid)

    def host_network(self):
        return psutil.net_io_counters()

def run_monitor(filename, interval=5):
    output = open(filename, 'w+')
    uma_pid = get_UMA_pid()
    cpu_info = CPUMonitor(uma_pid)
    mem_info = MemMonitor(uma_pid)
    disk_info = DiskMonitor(uma_pid)
    network_info = NetworkMonitor(uma_pid)
    while True:
        #host-wide cpu
        host_cpu_user = cpu_info.host_cpu_times_percent().user
        host_cpu_system = cpu_info.host_cpu_times_percent().system
        host_cpu_idle = cpu_info.host_cpu_times_percent().idle
        #uma daemon cpu
        umad_cpu = cpu_info.uma_cpu_percent()

        #host-wide memory
        host_mem_used = mem_info.host_mem().total
        host_mem_available = mem_info.host_mem().available
        host_mem_total = mem_info.host_mem().total
        host_mem_used_pct = host_mem_used * 1.0 / host_mem_total
        #host-wide memory swap
        host_mem_swap_total = mem_info.host_swap_mem().total
        host_mem_swap_used = mem_info.host_swap_mem().used
        host_mem_swap_free = mem_info.host_swap_mem().free
        #uma daemon mem
        umad_mem = mem_info.uma_mem().vms

        #host-wide disk
        host_rps = disk_info.host_iops().read_count
        host_wps = disk_info.host_iops().write_count
        host_rbps = disk_info.host_iops().read_bytes
        host_wbps = disk_info.host_iops().write_bytes
        #uma daemon disk
        umad_rps = disk_info.uma_iops().read_count
        umad_wps = disk_info.uma_iops().write_count
        umad_rbps = disk_info.uma_iops().read_bytes
        umad_wbps = disk_info.uma_iops().write_bytes

        #network(host-wide only)
        #host_network_sent = network_info.host_network()

        results = 'host_cpu_user=' + str(host_cpu_user) + ', '
        results += 'host_cpu_system=' + str(host_cpu_system) + ', '
        results += 'host_cpu_idle=' + str(host_cpu_idle) + ', '
        results += 'umad_cpu=' + str(umad_cpu) + ', '
        results += 'host_mem_used=' + str(host_mem_used) + ', '
        results += 'host_mem_available=' + str(host_mem_available) + ', '
        results += 'host_mem_total=' + str(host_mem_total) + ', '
        results += 'host_mem_used_pct=' + str(host_mem_used_pct) + ', '
        results += 'host_mem_swap_total=' + str(host_mem_swap_total) + ', '
        results += 'host_mem_swap_used=' + str(host_mem_swap_used) + ', '
        results += 'host_mem_swap_free=' + str(host_mem_swap_free) + ', '
        results += 'umad_mem=' + str(umad_mem) + ', '
        results += 'host_rps=' + str(host_rps) + ', '
        results += 'host_wps=' + str(host_wps) + ', '
        results += 'host_rbps=' + str(host_rbps) + ', '
        results += 'host_wbps=' + str(host_wbps) + ', '
        results += 'umad_rps=' + str(umad_rps) + ', '
        results += 'umad_wps=' + str(umad_wps) + ', '
        results += 'umad_rbps=' + str(umad_rbps) + ', '
        results += 'umad_wbps=' + str(umad_wbps) + '\n'

        output.write(results)
        output.flush()
        time.sleep(interval)

run_monitor("test.txt")