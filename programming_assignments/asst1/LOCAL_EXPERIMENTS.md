# 作业 1 本地实验条件

本作业作为本地自学实验完成，不使用 Stanford myth 机器。实验使用本地处理器和 Prog6 合成数据；性能结论对应各题记录的条件，不代表在 myth 或官方数据上取得相同结果。

## 硬件与工具

| 项目 | 实验配置 |
| --- | --- |
| CPU | 双路 Intel Xeon Gold 6330，每路 28 个物理核心，每核心两个硬件线程 |
| 整机规模 | 56 个物理核心、112 个逻辑 CPU |
| 多线程实验 CPU 集合 | `0-3,56-59`，均位于 socket 0 |
| 同核逻辑 CPU 配对 | `0/56`、`1/57`、`2/58`、`3/59` |
| 实验可用硬件 | 四个物理核心、八个逻辑 CPU；没有独占这些核心 |
| 系统 | Linux x86-64 |
| C++ 与构建工具 | g++ 13.3.0、GNU Make 4.3 |
| ISPC | 1.28.1，LLVM 20.1.8；Prog3–5 使用 `avx2-i32x8` 目标 |
| Python | CPython 3.11.15 |
| 绘图依赖 | NumPy 1.26.4、Matplotlib 3.6.3、scikit-learn 1.9.1、SciPy 1.17.1 |

本机工具目录为 `/data/users/huanghao/.local/opt/cs149-asst1`，进入环境的命令为：

```bash
source /data/users/huanghao/.local/opt/cs149-asst1/python/bin/activate
```

该绝对路径属于本机安装，其他机器需要自行安装对应工具。各程序沿用 Makefile 的编译参数；Prog3–5 使用普通 `make`，现有生成头文件的依赖规则不适合 `make -j`。

## 运行与测量

多线程实验通过 `taskset -c 0-3,56-59` 限制可用 CPU。Prog3 第一部分的普通 ISPC 实验单独固定到逻辑 CPU 0。CPU 亲和性不会模拟 myth 的频率、缓存或内存系统。

Prog3–5 共用的 `common/tasksys.cpp` 已适配 Linux CPU 亲和性：工作线程数为允许逻辑 CPU 数减一，主线程也参与计算。因此，上述八个逻辑 CPU 对应七个工作线程和主线程；仅允许一个 CPU 时，由主线程独立执行任务。回归检查见 [tasksys_affinity.cpp](common/tests/tasksys_affinity.cpp)。

Prog1 最终八线程、十六线程实验，以及 Prog3 原始两任务基线，每配置独立启动三次；后续新配置按用户要求只独立启动一次。Prog1 程序内部测五次取最短值，Prog3–5 内部测三次取最短值。Prog6 每版本只执行一次完整聚类，算法的 24 轮迭代不表示重复性能测量。

Prog2 使用课程模拟向量指令，记录模拟指令数和通道利用率，不以宿主 CPU 执行时间代替这些指标。其他题目的加速比使用同次运行的基准与优化耗时，不跨运行拼接基准。服务器采用动态频率，且未独占系统资源，单次结果不能确定性能稳定性。

所有实验日志和生成图像位于各程序的 `logs/` 中。运行会写入当前工作目录，因此在程序目录完成编译后，进入 `logs/` 再启动程序，可将新输出继续保存在该目录。当前远程会话没有 X 显示服务，PPM 可转换为 PNG 后预览。

## Prog6 本地合成数据

数据生成复用课程 `main.cpp` 中的生成函数和备用流程，没有使用 Stanford 官方数据。参数为 M=1000000、N=100、K=3、epsilon=0.1；`rand()` 种子为 7，正态随机引擎保留默认构造，噪声均值为 0、标准差为 0.5。生成器内部使用十个参考中心。

数据文件为 804002420 字节，SHA-256 为 `633b9395f15de5616929f9c84dd05ebed3ef0af51e55127b658b9673f5dbc1a8`。配置和生成时的源文件校验值见 [data-metadata.json](prog6_kmeans/logs/data-metadata.json)，生成脚本为 [generate-local-data.py](prog6_kmeans/logs/generate-local-data.py)。

数据文件、指向它的本地符号链接及编译产物不纳入 Git；源码、各版本源码快照、日志、图表和数据元信息保留在仓库。生成脚本在数据或元信息已经存在时会拒绝覆盖。需要重建数据时，应在临时副本中移开已有元信息后生成，并与仓库记录的校验值比较。

## 报告索引

完整汇总见 [writeup.md](writeup.md)。各题原始报告为：

- [Prog1 线程 Mandelbrot](prog1_mandelbrot_threads/REPORT.md)
- [Prog2 模拟 SIMD](prog2_vecintrin/REPORT.md)
- [Prog3 ISPC Mandelbrot](prog3_mandelbrot_ispc/REPORT.md)
- [Prog4 迭代平方根](prog4_sqrt/REPORT.md)
- [Prog5 SAXPY](prog5_saxpy/REPORT.md)
- [Prog6 K-Means](prog6_kmeans/REPORT.md)

Prog3 已测配置尚未达到 32× 参考值；Prog4 的手写 AVX2 和 Prog5 的性能优化选做未实现。Prog6 在本地合成数据上的总加速为 2.35×。当前未导出 `writeup.pdf`，也未验证 myth 环境。
