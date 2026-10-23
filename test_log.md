# 当前版本测试总入口

版本：2026-10-23 模型适用性修订。旧证据保留在 [history/](history/README.md)，没有把旧 AI 回复改写为本轮实验。

## 1. 公式与程序行为回归

[实际执行结果](validation/current/regression.txt)：12 个测试方法通过，含空值/缺键校验、单位数值类型、功率输入、单点、不同工作目录、模型警告、绘图幅值和周期性，以及 100 组设计的 10100 个公式模型工作点检查。这部分主要验证公式实现一致性，不能独立证明模型物理精度。

[公开及自拟脚本用例](validation/current/script-cases/executions.json)：T1–T5 的输入、命令、退出码、stdout/stderr 和 T1 PNG 均保留。它们是脚本实验，不能替代 AI 回复记录。

## 2. 独立耦合开关电路对照

[物理对照报告](validation/current/physics/REPORT.md)；[原始数值结果](validation/current/physics/summary.json)；[数值方法测试](validation/current/switched-tests.txt)。8 组参数、共 15 个端点候选对照，包含正常小纹波、大纹波、接近输入电压和接近 CCM 边界的案例。

这是独立于三角波假设的耦合状态方程数值解。它不是 SPICE 或硬件实验，也不证明整个连续范围或实际元件选型合格。

## 3. 三个新会话的 AI 行为测试

分别启动三个独立代理，每个不继承主聊天历史，只显式读取当前 skill 并处理一个问题。三个会话使用同一继承模型配置，没有跨模型或重复试验；不宣称测试了宿主自动发现。

| 会话 | 问题类型 | 本轮判定 | 完整实际回复 |
|---|---|---|---|
| F1 | 中文单位、正常输入 | Pass：正确计算并说明近似 | [回复](validation/current/fresh-sessions/F1/reply.md) |
| F2 | 同时缺少频率和电压纹波比 | Pass：一次列全并追问，未计算 | [回复](validation/current/fresh-sessions/F2/reply.md) |
| F3 | 输出电压纹波 20% | Pass：运行公式并披露全部模型警告，没有称为有效物理设计 | [回复](validation/current/fresh-sessions/F3/reply.md) |

每个文件夹含原始提问及实际工具证据。通过仅针对这三道显式调用题，不是 AI 总体准确率 100%，也不是此前八题的重新运行。

## 4. 可复现与版本标识

- [当前源文件哈希和运行环境](validation/current/manifest.json)
- [skill 格式校验](validation/current/skill-validation.txt)
- [近似条件及筛查值](references/model_scope.md)

基础回归：`python tests/test_design.py`；可选物理方法测试：`python tests/test_switched.py`；物理对照：`python tests/run_physics_suite.py --output-dir <new-output-dir>`。AI 回复是本次真实会话的证据，运行这些 Python 命令不会生成新的 AI 实验。
