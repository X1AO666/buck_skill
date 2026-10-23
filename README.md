# buck-inductor-design

2026-10-23 修订版，用于理想 CCM Buck 变换器作业。原始来源文件夹已保留。

## 使用

需要 Python 3.10+、NumPy 和 Matplotlib。如有需要，在你自己选定的环境中安装依赖：

```text
python -m pip install -r requirements.txt
```

发送整个 `buck-inductor-design/` 文件夹或它的压缩包，并要求 AI 先读取其中的 `SKILL.md`，再处理你的设计需求。必须同时提供 `scripts/design_buck.py` 等依赖文件，单独发送 `SKILL.md` 不足以执行技能。AI 需要文件读写与 Python 执行能力，并应先检查缺失值和歧义，再写 SI 单位的数值 JSON。纯聊天、无法执行脚本的 AI 无法完成规定流程。

在任意工作目录下运行时请使用绝对路径（把示例目录换成你解压后的文件夹）：

```text
python "C:/path/buck-inductor-design/scripts/design_buck.py" --input "C:/path/buck-inductor-design/tests/T1.json" --output-dir "C:/path/task/output"
python "C:/path/buck-inductor-design/tests/test_design.py"
```

只有命令行示例使用随附的 T1 数据，其他请求需要自备经过校验的输入文件。标准输出为结果 JSON；输入非法时以退出码 2 结束，并在标准错误中给出错误信息。退出码非零时不得报告任何有效结果。输出写入指定目录，每次测试请换一个全新目录，以免旧文件被误当成新结果。

## 文件与证据

- `SKILL.md`：触发描述、输入解释、校验、脚本调用与结果汇报约定。
- `scripts/design_buck.py`：数值校验、在小纹波近似下先算最小 L 再算 C、以及近似波形绘图。解析积分只针对预设三角形电容电流，不是完整开关电路的精确解。
- `tests/test_design.py`：可执行的回归测试，覆盖全范围约束、空输入、不同工作目录和极端占空比。
- `tests/T*.json`：原有的 5 个机器可读公开及补充用例。
- `hand_calculation.md`：原公开用例 T1 的手算过程。
- [test_log.md](test_log.md)：当前版本的唯一测试总入口，分别列出公式回归、独立物理对照及新会话 AI 测试。
- `scripts/compare_switched.py`：可选的独立耦合开关电路数值对照。
- [references/model_scope.md](references/model_scope.md)：近似条件、筛查阈值、对照方法和局限。
- `validation/current/`：本轮执行证据；旧记录在 `history/`，不能作为当前代码的新实验。
- `reflection.md`：如实的修订心得，没有虚构此前 AI 的理解偏差。

理想模型忽略 ESR/ESL、损耗、容差、瞬态响应和热限制。测试通过只说明被测试的行为可用，不代表实测的总体精度，也不等于硬件验证。特定宿主应用中的技能自动发现与显式调用是两回事，此处不作承诺。

## 小纹波近似的适用条件

本技能把周期内输出电压及负载电流近似视为常量，再由三角形电感纹波估计电容纹波。电容阻抗需相对负载阻抗足够小；接近输入电压或 CCM 边界时也需谨慎。脚本在较大预测纹波、阻抗比、纹波相对电感驱动电压或接近 CCM 边界时发出 `model_assessment.warnings`，并向 stderr 输出警告。阈值为项目自定筛查值，不是标准规定或误差保证。输入合法、退出码为 0 只表示公式计算完成，不能保证耦合电路中纹波上限或 CCM 一定成立。

为保持作业原规则，rv 仍只要求大于零；有警告时结果必须标成“待独立验证的公式估计”。即使没有警告，也不能称为物理验证通过。T1 中精确到公式最小值的选取，在耦合模型中就存在微小超限。

## 可选的独立物理对照

在选定环境安装 `python -m pip install -r requirements-validation.txt`，再运行：

```text
python "D:/buck-inductor-design/tests/test_switched.py"
python "D:/buck-inductor-design/tests/run_physics_suite.py" --output-dir "D:/buck-inductor-design/validation/my-new-run"
```

对照直接求解 `diL/dt=(u Vin-v)/L`、`dv/dt=(iL-v/R)/C`，用矩阵指数求周期初值，再由独立 ODE 积分与极值搜索测量纹波；不预设三角形电流。非正电流谷值会使二状态二极管 Buck 的 CCM 候选解无效，这种情况不会伪称 DCM 仿真结果。此对照也没有包含反馈控制、寄生参数或实际硬件。
