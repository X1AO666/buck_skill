# buck-inductor-design

用于理想 CCM Buck 变换器作业的电感 L、电容 C 选型的可复用 AI 技能。

## 文件说明
- `SKILL.md`：面向智能体的执行说明、检查项、停止规则与输出约定。
- `scripts/design_buck.py`：负责输入校验、参数计算与波形绘图的确定性脚本。
- `tests/`：T1–T5 机器可读测试用例。
- `hand_calculation.md`：公开用例 T1 的独立手算过程。
- `test_log.md`：测试结果与原因记录。
- `reflection.md`：150–250 词的心得草稿。
- `output/buck_waveforms.png`：T1 生成的波形图。

## 运行方式
需要 Python 3.10+、NumPy、Matplotlib。

```bash
python scripts/design_buck.py --input tests/T1.json --output-dir output
```

输入一律使用 SI 单位：伏特、欧姆、赫兹、瓦特；比例用小数表示（30% 写作 0.30）。
脚本会在开始计算前拒绝缺失的输入和超出范围的取值。
