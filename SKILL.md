---
name: buck-inductor-design
description: Size inductors and output capacitors for ideal CCM buck converters with fixed input voltage and resistive load, including requests with incomplete inputs. Validate completeness and consistency first; ask for missing or ambiguous values and stop on invalid specifications.
---

# Buck Converter Inductor and Capacitor Design

## Purpose
Calculate the minimum inductance `L` and output capacitance `C` that satisfy the requested inductor-current ripple ratio and output-voltage ripple ratio across the entire stated operating range for an ideal buck converter in continuous conduction mode (CCM).

## Required inputs
Before doing any calculation, confirm and restate with units:
- Input voltage `Vin` in V.
- Fixed resistive load `R` in ohms.
- Exactly one operating range is sufficient: output-voltage range `Vo_min`, `Vo_max` in V, or output-power range `P_min`, `P_max` in W. Both may be supplied, but if both are supplied they must agree.
- Switching frequency `fsw` in Hz.
- Inductor ripple ratio `rL` as a fraction (e.g. 30% = 0.30).
- Output voltage ripple ratio `rv` as a fraction (e.g. 1% = 0.01).

A single operating point is represented by setting a range's minimum equal to its maximum.

## Ordered procedure
1. **Check completeness first.** If any required item is missing, list every missing item and ask the user to provide it. Do not calculate, estimate, infer, or assume defaults.
2. **Parse units and ratios.** Convert kHz to Hz and percentages to fractions. Explicit natural-language equivalents such as “十万赫兹” = 100000 Hz and “百分之三十” = 0.30 are values, not defaults. A bare `30` is not automatically `30%`; ask if intent or units are ambiguous. List all missing items together. A null endpoint counts as missing even when its key exists. Ask the user to complete or withdraw an incomplete additional range rather than ignoring its supplied values.
3. **Check basic validity.** All numeric inputs must be finite and strictly positive. Each minimum must be less than or equal to its corresponding maximum. Require `0 < Vo_min <= Vo_max < Vin`. Require `0 < rL < 2` and `rv > 0`. If a supplied power range is used, require `0 < P_min <= P_max`.
4. **Check range consistency.** When voltage and power ranges are both supplied, verify `P = Vo^2/R` at corresponding endpoints (minimum with minimum and maximum with maximum) within a relative tolerance of 1e-6. If they disagree, stop and explain the conflict.
5. **Do not silently repair bad inputs.** Do not swap minimum and maximum, clamp output voltage to `Vin`, reinterpret a percentage as a whole number, or select an unstated operating range.
6. **Determine the operating range.** If only power is supplied, derive voltage endpoints using `Vo = sqrt(P R)`. If both ranges are supplied and consistent, use the voltage range.
7. **Compute the design using the calculation script.** Let `SKILL_DIR` be the absolute directory containing this loaded `SKILL.md`, not the current working directory. Create a JSON input in the task workspace using the schema below, then run the equivalent of `python "<SKILL_DIR>/scripts/design_buck.py" --input "<absolute-input.json>" --output-dir "<absolute-output-directory>"`. Quote paths with spaces. Never reuse T1 values for another request. Requires Python 3.10+, NumPy and Matplotlib; report unavailable dependencies without inventing results. Read stdout JSON and verify exit code 0 before reporting success. Do not perform the final arithmetic mentally or invent script output.
8. **Explain the worst case.** Report the interpreted inputs and units, minimum L and C, the worst-case operating point for each constraint, the calculated peak-to-peak ripples, and assumptions.
9. **Create the required plot.** The plot must have a 2×1 layout with shared time axis, show three steady-state switching periods in microseconds, plot inductor current on top and output ripple `vo(t)-Vo` in mV on bottom, show both range endpoints in different colors with a legend, and include computed `ΔIL` and `ΔVo` in the legend or on the plot. Save as PNG.
10. **Report limits.** State that the results use the assignment's ideal-switch, ideal-diode, ideal-inductor, steady-state, CCM assumptions and ignore capacitor ESR/ESL. Do not imply the design is validated for real component tolerances, losses, transient response, or thermal limits.

## Script input schema
Use a JSON object with numeric SI-unit fields `Vin`, `R`, `fsw`, `rL`, `rv`, and either the pair `Vo_min`, `Vo_max` or `P_min`, `P_max`. Both complete pairs are allowed. Ratios are fractions. Omit unused ranges entirely instead of sending null placeholders. The script does not parse human-language units; resolve ambiguity before constructing JSON.

Bundled public test example only:
```json
{"Vin":24,"R":3,"Vo_min":6,"Vo_max":12,"fsw":100000,"rL":0.30,"rv":0.01}
```

## Reference equations
- `D = Vo / Vin`
- `Io = Vo / R`
- `P = Vo^2 / R`
- `ΔIL = Vo (1-D) / (L fsw)`
- `ΔVo = ΔIL / (8 fsw C)`
- CCM condition: `Io - ΔIL/2 > 0`
- `rL = ΔIL / Io`, `rv = ΔVo / Vo`

For a voltage-range input, the minimum inductance is selected so `ΔIL / Io <= rL` at every operating point. With fixed R, the limiting L is at `Vo_min`. Then select the minimum C so `ΔVo / Vo <= rv` at every operating point using the selected L. These are sequential minima: increasing L can permit a smaller C, so do not claim independent global minima.

## Stop and refusal rules
- Missing required inputs: ask for them and do not calculate.
- Non-positive, non-finite, reversed ranges, `Vo_max >= Vin`, `rL >= 2`, or inconsistent voltage/power ranges: stop with a clear error.
- If a requested specification is outside the ideal buck/CCM assumptions, explain why and ask for corrected requirements. Do not output a purported valid design.
- If the script fails or its output cannot be verified, report the failure; do not fabricate numbers or plots.

## Output format
1. Input interpretation (with units and ratio conversions).
2. Validation result.
3. L and C with units and governing equations.
4. Worst-case operating point and computed ripples.
5. Assumptions and limitations.
6. PNG plot path.

## Explicit "do not" rules
- Do not assume a value for a missing input.
- Do not calculate before completing input and consistency checks.
- Do not use unverified mental arithmetic as the final result.
- Do not hide or silently fix invalid inputs.
- Do not claim a physical design is safe or production-ready based on this ideal model alone.
