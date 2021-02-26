# https://www.thepythoncode.com/article/get-hardware-system-information-python

import platform,socket,re,uuid,json,psutil,logging
from datetime import datetime

def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def getSystemInfo():
    try:
        bt = datetime.fromtimestamp(psutil.boot_time())
        svmem = psutil.virtual_memory()

        partitions = psutil.disk_partitions()
        diskPartitions = {}
        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                # this can be catched due to the disk that
                # isn't ready
                continue
            diskPartitions[partition.mountpoint] = {}
            diskPartitions[partition.mountpoint]['size'] = get_size(partition_usage.total)
            diskPartitions[partition.mountpoint]['used'] = get_size(partition_usage.used)
            #print(f"  Free: {get_size(partition_usage.free)}")
            diskPartitions[partition.mountpoint]['used-percentage'] = f"{partition_usage.percent}%"

        info={}
        info['platform-system']=platform.system()
        info['platform-node']=platform.node()
        info['platform-release']=platform.release()
        info['platform-version']=platform.version()
        info['platform-machine']=platform.machine() 
        info['platform-processor']=platform.processor()
        info['boot_time']=f"Boot Time: {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}"
        info['hostname']=socket.gethostname()
        info['ip-address']=socket.gethostbyname(socket.gethostname())
        info['mac-address']=':'.join(re.findall('..', '%012x' % uuid.getnode()))
        info['ram-total']=get_size(svmem.total)
        info['ram-free']=get_size(svmem.available)
        info['disk_partitions']=diskPartitions
        return json.dumps(info,indent=4, separators=(',', ': '))
    except Exception as e:
        logging.exception(e)
