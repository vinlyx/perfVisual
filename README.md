# perfVisual - 程序性能监控与可视化工具

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个用于监控指定进程系统资源使用情况的Python工具，可生成结构化数据用于分析。

## 功能特性

- 实时监控并记录进程资源使用数据到SQLite数据库
- 支持自定义监控间隔（毫秒级精度）
- 提供命令行界面和程序API两种使用方式
- 生成可直接导入分析工具的结构化数据
- 监控指标包括：
  - CPU使用率
  - 内存占用
  - 磁盘I/O速度
  - 线程数量

## 安装要求

- Python 3.6+
- 依赖库：
  - psutil
  - sqlite3 (Python内置)

安装依赖：
```bash
pip install psutil
```

## 使用说明

### 基本用法

```bash
./perfvisual.py "python3 my_script.py" > stats.csv
```

### 带参数用法

```bash
./perfvisual.py --interval 500 "java -jar myapp.jar" | tee log.txt
```

### 参数说明

| 参数 | 描述 |
|------|------|
| `<执行命令>` | 需要监控的命令及其参数（需用引号包裹） |
| `-i, --interval` | 监控间隔（毫秒，默认100ms），建议范围：100-5000 |

### 输出说明

- 标准输出包含TSV格式的实时监控数据
- 同时会写入SQLite数据库（默认按时间生成文件名）
- 数据库包含完整监控指标，包括：
  - 时间戳
  - 线程数
  - CPU百分比
  - 内存占用(MB)
  - 读/写操作次数
  - 读/写字节数
  - 读/写速率(MB/s)

## 典型使用场景

1. 性能基准测试
2. 资源泄漏检测
3. 程序行为分析

## 开发API

```python
from perfvisual import PerfVisual

# 初始化监控器
pv = PerfVisual(intervalMs=500)  # 500ms采样间隔

# 执行监控
pv.exec("python3 my_script.py", recordDB="performance.db")
```

## 数据库结构

详细数据库格式请参考[dbFormat.md](dbFormat.md)

## 版本信息

当前版本：0.1.0
最后更新：2025-03-25


## 许可证

本项目采用 [MIT License](LICENSE)

