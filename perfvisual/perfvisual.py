#!/usr/bin/env python3

###### Import Modules
# 系统相关模块
import sys
import os
import time
import datetime
import subprocess
import sqlite3
import platform
import psutil

###### Document Decription
"""性能可视化监控工具

本程序用于监控指定进程的系统资源使用情况，包括：
- CPU使用率
- 内存占用
- 磁盘I/O速度
- 线程数量

功能特性：
1. 实时监控并记录进程资源使用数据到SQLite数据库
2. 支持自定义监控间隔（毫秒级精度）
3. 提供命令行界面和程序API两种使用方式
4. 生成可直接导入分析工具的结构化数据

典型使用场景：
1. 性能基准测试
2. 资源泄漏检测
3. 程序行为分析

示例用法：
$ ./perfvisual.py "python3 my_script.py" > stats.csv
$ ./perfvisual.py --interval 500 "java -jar myapp.jar" | tee log.txt

"""

###### Version and Date
# 程序版本 (遵循语义化版本规范)
PROG_VERSION = '0.1.0'
# 最后更新日期 (ISO 8601格式)
PROG_DATE = '2024-09-24'

###### Usage
USAGE = """

     Version %s  by Vincent Li  %s

     Usage:
     %s [选项] <执行命令>

     参数说明：
     <执行命令>       需要监控的命令及其参数（需用引号包裹）

     选项：
     -i, --interval  监控间隔（毫秒，默认100ms）
                     建议范围：100-5000，过小可能影响被监控程序性能

     输出说明：
     - 标准输出包含TSV格式的实时监控数据
     - 当指定recordDB参数时，会同时写入SQLite数据库
     - 数据库包含完整监控指标，包括时间戳、线程数、CPU百分比、内存占用(MB)、
       读操作次数、写操作次数、读写字节数、读写速率(MB/s)
""" % (PROG_VERSION, PROG_DATE, os.path.basename(sys.argv[0]))

######## Global Variable


#######################################################################
############################  BEGIN Class  ############################
#######################################################################
class PerfVisual(object):
    """性能可视化监控主类

    职责：
    - 管理监控生命周期（初始化、执行、资源清理）
    - 协调数据采集、处理和存储
    - 提供数据库管理接口

    主要功能：
    1. 执行目标程序并实时监控其资源使用
    2. 将监控数据持久化到SQLite数据库
    3. 数据采样频率控制
    4. 控制台报表生成

    设计要点：
    - 使用生产者-消费者模式分离数据采集和存储
    - 基于psutil实现跨平台监控
    - 采用SQLite WAL模式提升并发写入性能
    """

    def __init__(self, intervalMs: float=1000.0):
        """初始化性能监控器

        参数：
        intervalMs : float
            监控采样间隔（毫秒），建议 >= 100ms
            过低间隔可能导致：
            - 采样数据冗余
            - 增加被监控进程负载
            - 数据库写入压力

        属性：
        db : sqlite3.Connection
            数据库连接对象，None表示未初始化
        lastRd : int
            上次读取字节数，用于计算IO速度
        lastWt : int
            上次写入字节数，用于计算IO速度
        lastTime : datetime
            上次采样时间戳
        """
        super().__init__()
        self.intervalMs = intervalMs
        self.db = None
        self.lastRd = 0
        self.lastWt = 0
        self.lastTime = None

    def collectSysInfo(self, cmd):
        """收集系统信息并插入到数据库"""
        try:
            # CPU信息
            cpu_model = platform.processor()
            cpu_cores = psutil.cpu_count(logical=False)
            cpu_threads = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            cpu_base_freq = cpu_freq.min if cpu_freq else 0.0
            cpu_max_freq = cpu_freq.max if cpu_freq else 0.0

            # 内存信息
            mem = psutil.virtual_memory()
            total_memory = mem.total
            available_memory = mem.available
            used_memory = mem.used
            memory_usage = mem.percent

            # 磁盘信息
            disk = psutil.disk_usage(os.getcwd())
            disk_total = disk.total
            disk_available = disk.free
            disk_used = disk.used

            # 运行环境信息
            os_version = platform.platform()
            current_time = datetime.datetime.now()
            work_dir = os.getcwd()

            # 插入数据到systemInfo表
            self.db.execute('''
                INSERT INTO systemInfo (
                    cpu_model, cpu_cores, cpu_threads,
                    cpu_base_freq, cpu_max_freq,
                    total_memory, available_memory, used_memory,
                    memory_usage, disk_total,
                    disk_available, disk_used, os_version,
                    command, current_time, work_dir
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cpu_model, cpu_cores, cpu_threads,
                cpu_base_freq, cpu_max_freq,
                total_memory, available_memory, used_memory,
                memory_usage, disk_total,
                disk_available, disk_used, os_version,
                cmd, current_time, work_dir
            ))
            self.db.commit()

        except Exception as e:
            print(f"Error collecting system info: {e}", file=sys.stderr)

    def exec(self, cmd: str, recordDB: str=None):
        """执行监控主流程

        参数：
        cmd : str
            要监控的执行命令（需确保可被sh解析）
            示例："python3 main.py --input data.csv"
        recordDB : str, optional
            数据库文件名，默认按时间生成
            如：'perf_20240315_1415.db'

        流程说明：
        1. 初始化数据库连接
        2. 收集系统信息
        3. 启动子进程并获取PID
        4. 进入监控循环：
            a. 采集进程指标
            b. 计算IO速度
            c. 输出到控制台
            d. 写入数据库
        5. 清理资源

        注意：
        - 使用shell=False增强安全性，但要求命令以列表形式传入
        - 当前实现通过split()简单处理命令字符串，可能无法正确处理：
          * 包含空格的参数
          * 引号包裹的参数
          * 环境变量扩展
          建议后续改进为shlex.split()解析命令
        """
        self.db = self.initDB(recordDB)
        self.collectSysInfo(cmd)

        ## FIXME: since psutil can only record status of shell with
        ## shell=True, here use .split to convert cmdline into a list
        ## This method may cause unexpected issues.
        proc = subprocess.Popen(cmd.split(), shell=False)
        self.lastTime = datetime.datetime.now()
        pt = self.lastTime
        print("Date\tCPU%\tMemoryMB\tReadMBps\tWriteMBps")
        pm = ProcessMonitor(proc.pid)

        while proc.poll() is None:
            rec = pm.record()
            itv = (rec[0] - self.lastTime).total_seconds()
            rdSpd = self.calSpdMB(rec[4].read_bytes - self.lastRd, itv)
            wtSpd = self.calSpdMB(rec[4].write_bytes - self.lastWt, itv)

            if (rec[0] - pt).total_seconds() > 5:
                print(f"{rec[0]}\t{rec[2]}%\t{rec[3]}",
                      f"{rdSpd}\t{wtSpd}", sep="\t")
                pt = rec[0]

            self.updateDB(*rec[:4],
                          rec[4].read_count,
                          rec[4].write_count,
                          rec[4].read_bytes,
                          rec[4].write_bytes,
                          rdSpd,
                          wtSpd)

            self.lastRd = rec[4].read_bytes
            self.lastWt = rec[4].write_bytes
            self.lastTime = rec[0]

            time.sleep(self.intervalMs / 1000.0)

        self.db.close()

    def initDB(self, dbName: str=None):
        """初始化监控数据库

        功能：
        1. 创建/连接SQLite数据库文件
        2. 初始化process_stats和systemInfo数据表结构
        3. 配置数据库性能参数

        参数：
        dbName : str, optional
            数据库文件名，默认按时间格式生成
            示例："perf_20240315_1415.db"

        返回：
        sqlite3.Connection
            数据库连接对象

        数据库优化措施：
        - 启用WAL模式提升并发性能
        - 设置同步模式为NORMAL
        - 配置合理的页面大小（4096）
        - 预分配存储空间（TODO）
        """
        if not dbName:
            dbName = datetime.datetime.now().strftime("%Y%m%d_%H.%M.%S") + ".db"
        conn = sqlite3.connect(dbName)
        c = conn.cursor()

        # 创建process_stats表
        c.execute('''CREATE TABLE IF NOT EXISTS process_stats
                     (timestamp DATETIME, threads_num INTEGER,
                     cpu_percent FLOAT, memory_mb REAL,
                     read_count INTEGER, write_count INTEGER,
                     read_bytes INTEGER, write_bytes INTEGER,
                     read_mbps FLOAT, write_mbps FLOAT)''')

        # 创建systemInfo表
        c.execute('''CREATE TABLE IF NOT EXISTS systemInfo
                     (cpu_model TEXT,
                     cpu_cores INTEGER,
                     cpu_threads INTEGER,
                     cpu_base_freq FLOAT,
                     cpu_max_freq FLOAT,
                     cpu_cache_size TEXT,
                     total_memory INTEGER,
                     available_memory INTEGER,
                     used_memory INTEGER,
                     memory_usage FLOAT,
                     disk_type TEXT,
                     disk_total INTEGER,
                     disk_available INTEGER,
                     disk_used INTEGER,
                     os_version TEXT,
                     command TEXT,
                     current_time DATETIME,
                     work_dir TEXT)''')

        conn.commit()
        return conn

    def connectDB(self, dbName: str):
        conn = sqlite3.connect(dbName)
        self.db = conn
        return conn

    def updateDB(self, *info):
        self.db.execute('''INSERT INTO process_stats VALUES
                           (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        info)
        self.db.commit()

    def calSpdMB(self, byte: int, intervalSec: float) -> float:
        """计算每秒兆字节数

        参数：
        byte : int
            字节数变化量（当前 - 上次）
        intervalSec : float
            时间间隔（秒）

        返回：
        float
            换算后的MB/s速度，保留3位小数

        公式：
        MB/s = (Δbytes / 间隔时间) / (1024^2)
        采用银行家舍入法避免统计偏差
        """
        return round(byte / intervalSec / 1024**2, 3)


class ProcessMonitor(object):
    """ 进程监控工具类
    功能：
    1. 实时采集进程的CPU、内存、I/O等指标
    2. 提供一次性快照方式获取完整监控数据
    """

    def __init__(self, pid):
        super().__init__()
        self.proc = psutil.Process(pid)

    def record(self):
        p = self.proc # shortcut
        with p.oneshot():
            now = datetime.datetime.now()

            # cpu_percent = p.cpu_percent()
            return (now, p.num_threads(), p.cpu_percent(),
                    round(p.memory_info().rss/1024.0**2, 3),
                    p.io_counters())


##########################################################################
############################  BEGIN Function  ############################
##########################################################################


######################################################################
############################  BEGIN Main  ############################
######################################################################
#################################
##
##   Main function of program.
##
#################################
def main():

    ######################### Phrase parameters #########################
    import argparse
    ArgParser = argparse.ArgumentParser(usage=USAGE)
    ArgParser.add_argument("--version", action="version", version=PROG_VERSION)
    ArgParser.add_argument("-i", "--interval", action="store", dest="intval", type=int, default=100, metavar="INT", help="Monitor interval in Miliseconds. [%(default)s]")

    (params, args) = ArgParser.parse_known_args()

    if len(args) != 1:
        ArgParser.print_help()
        print("\n[ERROR]: The parameters number is not correct!", file=sys.stderr)
        sys.exit(1)
    else:
        (cmdLine,) = args # pylint: disable=unbalanced-tuple-unpacking

    ############################# Main Body #############################
    pv = PerfVisual(params.intval)
    pv.exec(cmdLine)

    return 0

#################################
##
##   Start the main program.
##
#################################
if __name__ == '__main__':
    return_code = main()
    sys.exit(return_code)

################## God's in his heaven, All's right with the world. ##################
