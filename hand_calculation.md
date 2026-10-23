# Hand calculation — public test T1

Given: `Vin = 24 V`, `R = 3 Ω`, `Vo = 6–12 V`, `fsw = 100 kHz`, `rL = 0.30`, `rv = 0.01`. The ratios are fractions, so 30% = 0.30 and 1% = 0.01.

For a resistive load, `Io = Vo/R` and `D = Vo/Vin`. The inductor ripple is `ΔIL = Vo(1-D)/(L fsw)`. Requiring `ΔIL/Io ≤ rL` gives

`L ≥ R(1 − Vo/Vin)/(fsw rL)`.

For fixed R, Vin, fsw and rL, the right-hand side is largest at the lowest output voltage, 6 V:

`Lmin = 3 Ω × (1 − 6/24) / (100000 Hz × 0.30) = 75 × 10⁻⁶ H = 75 µH`.

At 6 V, `Io = 6/3 = 2 A`, `D = 0.25`, and `ΔIL = 6(1−0.25)/(75 µH × 100 kHz) = 0.60 A p-p`.

At 12 V, `Io = 4 A`, `D = 0.50`, and `ΔIL = 12(1−0.50)/(75 µH × 100 kHz) = 0.80 A p-p`, so the actual ripple ratio there is 0.80/4 = 0.20.

The capacitor equation is `ΔVo = ΔIL/(8 fsw C)`. Thus `C ≥ ΔIL/(8 fsw rv Vo)`. At 6 V, `C ≥ 0.60/(8 × 100000 × 0.01 × 6) = 12.5 µF`. At 12 V, `C ≥ 0.80/(8 × 100000 × 0.01 × 12) = 8.33 µF`. Therefore the minimum capacitance is `12.5 µF`, also limited by the 6 V endpoint.

**Hand result:** `Lmin = 75 µH`, `Cmin = 12.5 µF`; both worst-case constraints occur at `Vo = 6 V`. Assumptions: ideal switch, diode and inductor; steady state; CCM; capacitor ESR/ESL ignored.
