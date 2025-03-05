# 性能监控数据库结构文档

## 数据库表结构 - process_stats

| 字段名称         | 数据类型    | 描述                          | 测量单位  |
|------------------|-------------|-----------------------------|-----------|
| timestamp        | DATETIME    | 记录时间戳                     | 本地时间  |
| threads_num      | INTEGER     | 进程线程数                     | 个        |
| cpu_percent      | FLOAT       | CPU使用率                     | 百分比    |
| memory_mb        | REAL        | 内存使用量                    | MB        |
| read_count       | INTEGER     | 累计读取操作次数               | 次        |
| write_count      | INTEGER     | 累计写入操作次数               | 次        |
| read_bytes       | INTEGER     | 累计读取字节数                 | 字节      |
| write_bytes      | INTEGER     | 累计写入字节数                 | 字节      |
| read_mbps        | FLOAT       | 读取速率                      | MB/s      |
| write_mbps       | FLOAT       | 写入速率                      | MB/s      |

## 数据库表结构 - systemInfo

| 字段名称         | 数据类型    | 描述                          | 测量单位  |
|------------------|-------------|-----------------------------|-----------|
| cpu_model        | TEXT        | CPU型号                       | -         |
| cpu_cores        | INTEGER     | CPU物理核心数                 | 个        |
| cpu_threads      | INTEGER     | CPU逻辑线程数                 | 个        |
| cpu_base_freq    | FLOAT       | CPU基础频率                   | GHz       |
| cpu_max_freq     | FLOAT       | CPU最大频率                   | GHz       |
| total_memory     | INTEGER     | 系统总内存                    | 字节      |
| available_memory | INTEGER     | 系统可用内存                  | 字节      |
| used_memory      | INTEGER     | 系统已用内存                  | 字节      |
| memory_usage     | FLOAT       | 内存使用率                    | 百分比    |
| disk_total       | INTEGER     | 磁盘总容量                    | 字节      |
| disk_available   | INTEGER     | 磁盘可用容量                  | 字节      |
| disk_used        | INTEGER     | 磁盘已用容量                  | 字节      |
| os_version       | TEXT        | 操作系统版本                  | -         |
| command          | TEXT        | 执行命令                      | -         |
| current_time     | DATETIME    | 当前时间                      | 本地时间  |
| work_dir         | TEXT        | 当前工作目录                  | -         |

## 数据采集说明

### 采集频率
- 默认采样间隔：1000毫秒（可通过初始化参数调整）
- 采样时间 = 程序执行时间 ± 采样间隔

### 数据来源
1. **进程信息**（通过psutil库获取）
   - 线程数
   - CPU使用率
   - 内存占用(RSS)
2. **I/O统计**（通过psutil.io_counters()）
   - 读取次数/字节数
   - 写入次数/字节数

### 速率计算
```python
# 读取速率公式
read_mbps = (本次read_bytes - 上次read_bytes) / 时间间隔(秒) / 1024²

# 写入速率公式
write_mbps = (本次write_bytes - 上次write_bytes) / 时间间隔(秒) / 1024²
```

## 数据存储特性
1. 数据库文件自动生成（当不指定文件名时）
   - 命名规则：YYYYMMDD_HH.MM.SS.db
   - 示例：20240924_14.30.00.db
2. 数据持久化方式
   - 每次采样立即提交(autocommit)
   - SQLite WAL模式写入

## 典型应用场景
1. 长期运行进程的资源监控
2. 性能瓶颈分析（CPU/内存/I/O）
3. 异常行为检测（内存泄漏、I/O暴增等）
