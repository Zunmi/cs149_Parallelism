Stanford CS149 Fall 2025 学习资料

已完成下载：18 份 lecture PDF、4 份 written assignment PDF、5 个编程作业仓库、41 份参考 PDF/HTML，以及课程页面快照。
学习入口：用浏览器打开当前目录的 index.html。

lectures/                 讲义 PDF，按 01–18 编号排列
written_assignments/      4 份书面作业，含原文件中的练习内容
programming_assignments/  作业仓库，按各目录 README.md 开始阅读
readings/                 ISPC、CUDA、NKI、Triton 等作业引用的参考资料
course_pages/             课表、课程信息、讲义列表和 18 个 lecture 页面快照

编程作业入口：
  programming_assignments/asst1/README.md
  programming_assignments/asst2/README.md
  programming_assignments/asst3/README.md
  programming_assignments/asst4-trainium2/README.md
  programming_assignments/asst5-kernels/README.md

校验记录：downloaded_materials.json / download_status.json
所有 PDF 已逐页检查页面树能否解析，所有 ZIP 通过 CRC 校验。
完整清单记录原始 URL、必要的归档替代 URL、文件大小、页数及 SHA-256。

公开 lecture 页面没有额外的阅读清单；参考资料取自编程作业引用。
三处失效 AWS 链接采用官方 v2.26.0 文档归档，详见 readings/source_replacements.json。
外部文档可能更新到较新版本，做作业时以仓库要求的工具版本为准。
HTML 为页面快照，部分图片、样式、交互功能及外部链接仍需联网。
2025 年课程录像仅通过 Canvas 提供；本次资料不含录像。

补齐误删的文件时可重跑：
  cd /home/huanghao/cs149
  python3 download_course.py

下载器使用 Python 3.9+，个别站点兼容处理需要系统 curl；默认六路并行并强制跳过代理。
已有文件会验证后跳过，已有且标记匹配的作业目录会保留本地修改。
已有且没有下载标记的作业目录不会被覆盖。
原始链接清单：materials.json；完整下载清单：downloaded_materials.json。
下载日期：2026-10-23
课程来源：https://gfxcourses.stanford.edu/cs149/fall25/courseinfo
