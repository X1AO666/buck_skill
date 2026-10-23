# buck-inductor-design

2026-10-23 修订版，用于理想 CCM Buck 变换器作业。原始来源文件夹已保留。

## 使用

需要 Python 3.10+、NumPy 和 Matplotlib。如有需要，在你自己选定的环境中安装依赖：

```text
python -m pip install -r requirements.txt
```

把本文件夹的 `SKILL.md` 连同你的设计需求交给具备文件读写与脚本执行能力的 AI。AI 应先检查缺失值和歧义，然后再写出以 SI 为单位、带数值的 JSON。只能聊天、无法执行脚本的 AI 跑不了本技能的计算流程。

在任意工作目录下运行时请使用绝对路径（把示例目录换成你解压后的文件夹）：

```text
python "C:/path/buck-inductor-design/scripts/design_buck.py" --input "C:/path/buck-inductor-design/tests/T1.json" --output-dir "C:/path/task/output"
python "C:/path/buck-inductor-design/tests/test_design.py"
```

只有命令行示例使用随附的 T1 数据，其他请求需要自备经过校验的输入文件。标准输出为结果 JSON；输入非法时以退出码 2 结束，并在标准错误中给出错误信息。退出码非零时不得报告任何有效结果。输出写入指定目录，每次测试请换一个全新目录，以免旧文件被误当成新结果。

## 文件与证据

- `SKILL.md`：触发描述、输入解释、校验、脚本调用与结果汇报约定。
- `scripts/design_buck.py`：数值校验、先算最小 L 再算 C、以及解析式稳态波形绘图。
- `tests/test_design.py`：可执行的回归测试，覆盖全范围约束、空输入、不同工作目录和极端占空比。
- `tests/T*.json`：原有的 5 个机器可读公开及补充用例。
- `hand_calculation.md`：原公开用例 T1 的手算过程。
- `validation/`：本次执行证据与独立智能体测试记录，含适用范围与局限。
- `reflection.md`：如实的修订心得，没有虚构此前 AI 的理解偏差。

理想模型忽略 ESR/ESL、损耗、容差、瞬态响应和热限制。测试通过只说明被测试的行为可用，不代表实测的总体精度，也不等于硬件验证。特定宿主应用中的技能自动发现与显式调用是两回事，此处不作承诺。
