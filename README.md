# buck-inductor-design

Reusable AI skill for sizing L and C for the ideal CCM buck-converter assignment.

## Files
- `SKILL.md`: agent-facing instructions, checks, stop rules, and output contract.
- `scripts/design_buck.py`: deterministic input validation, sizing, and plot generation.
- `tests/`: T1–T5 machine-readable test cases.
- `hand_calculation.md`: independent hand calculation for public test T1.
- `test_log.md`: test outcomes and reasons.
- `reflection.md`: 150–250 word reflection draft.
- `output/buck_waveforms.png`: generated plot for T1.

## Run
Requires Python 3.10+, NumPy, and Matplotlib.

```bash
python scripts/design_buck.py --input tests/T1.json --output-dir output
```

Inputs use SI units: volts, ohms, hertz, watts; ratios are fractions (30% = 0.30).
The script rejects missing inputs and invalid ranges before calculating.
