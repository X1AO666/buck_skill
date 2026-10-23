#!/usr/bin/env python3
"""Validated sizing and waveform plot for the assignment's ideal CCM buck model."""
import argparse
import json
import math
import os
import sys

def finite_positive(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number; received {value!r}.")

def validate(data):
    required = ["Vin", "R", "fsw", "rL", "rv"]
    missing = [k for k in required if k not in data or data[k] is None]
    has_v = ("Vo_min" in data and data.get("Vo_min") is not None and
             "Vo_max" in data and data.get("Vo_max") is not None)
    has_p = ("P_min" in data and data.get("P_min") is not None and
             "P_max" in data and data.get("P_max") is not None)
    partial_v = (("Vo_min" in data) != ("Vo_max" in data))
    partial_p = (("P_min" in data) != ("P_max" in data))
    if partial_v:
        missing.append("Vo_min or Vo_max (both endpoints are required)")
    if partial_p:
        missing.append("P_min or P_max (both endpoints are required)")
    if not has_v and not has_p and not partial_v and not partial_p:
        missing.append("an operating range: Vo_min and Vo_max, or P_min and P_max")
    if missing:
        raise ValueError("Missing required input(s): " + ", ".join(missing) + ". No calculation performed.")
    for k in required:
        finite_positive(k, data[k])
    for k in (["Vo_min", "Vo_max"] if has_v else []) + (["P_min", "P_max"] if has_p else []):
        finite_positive(k, data[k])
    if data["rL"] >= 2:
        raise ValueError(f"rL must be less than 2 for the stated CCM requirement; received {data['rL']}.")
    if data["rv"] <= 0:
        raise ValueError("rv must be positive.")
    if has_v:
        if data["Vo_min"] > data["Vo_max"]:
            raise ValueError("Invalid voltage range: Vo_min must be <= Vo_max.")
        if data["Vo_max"] >= data["Vin"]:
            raise ValueError(f"Impossible buck-converter range: Vo_max={data['Vo_max']} V must be less than Vin={data['Vin']} V.")
    if has_p and data["P_min"] > data["P_max"]:
        raise ValueError("Invalid power range: P_min must be <= P_max.")
    if has_p:
        pvmin, pvmax = math.sqrt(data["P_min"] * data["R"]), math.sqrt(data["P_max"] * data["R"])
        if pvmax >= data["Vin"]:
            raise ValueError(f"Impossible buck-converter range: derived Vo_max={pvmax:g} V must be less than Vin={data['Vin']} V.")
        if has_v:
            for label, v, p in [("minimum", data["Vo_min"], data["P_min"]), ("maximum", data["Vo_max"], data["P_max"])]:
                expected = v*v/data["R"]
                if not math.isclose(expected, p, rel_tol=1e-6, abs_tol=1e-12):
                    raise ValueError(f"Inconsistent voltage and power ranges at {label} endpoint: Vo^2/R={expected:g} W but supplied P={p:g} W.")
    if has_v:
        vmin, vmax = data["Vo_min"], data["Vo_max"]
    else:
        vmin, vmax = math.sqrt(data["P_min"]*data["R"]), math.sqrt(data["P_max"]*data["R"])
    if vmin <= 0 or vmax >= data["Vin"]:
        raise ValueError("Derived operating range must satisfy 0 < Vo_min <= Vo_max < Vin.")
    return vmin, vmax

def design(data, vmin, vmax):
    Vin, R, fs, rL, rv = (float(data[k]) for k in ("Vin", "R", "fsw", "rL", "rv"))
    # ΔIL/Io = R(1-Vo/Vin)/(L fs); the largest requirement is at Vo_min.
    L = R * (1 - vmin/Vin) / (fs*rL)
    points = []
    for vo in (vmin, vmax):
        d = vo/Vin
        io = vo/R
        dil = vo*(1-d)/(L*fs)
        dvo = dil/(8*fs) # numerator; divide by C below
        c_required = dil/(8*fs*rv*vo)
        points.append({"Vo": vo, "D": d, "Io": io, "dIL": dil,
                       "C_required": c_required, "rL_actual": dil/io})
    C = max(p["C_required"] for p in points)
    for p in points:
        p["dVo"] = p["dIL"]/(8*fs*C)
        p["rv_actual"] = p["dVo"]/p["Vo"]
        p["P"] = p["Vo"]**2/R
    return {"L_H": L, "C_F": C, "points": points,
            "worst_L_Vo": min(points, key=lambda p: p["rL_actual"]-rL)["Vo"] if False else vmin,
            "worst_C_Vo": max(points, key=lambda p: p["C_required"])["Vo"]}

def make_plot(data, result, vmin, vmax, outdir):
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(outdir, exist_ok=True)
    Vin, R, fs = float(data["Vin"]), float(data["R"]), float(data["fsw"])
    L, C = result["L_H"], result["C_F"]
    period = 1/fs
    t = np.linspace(0, 3*period, 1201)
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 6.5), constrained_layout=True)
    colors = ["tab:blue", "tab:orange"]
    for vo, color, label in zip([vmin, vmax], colors, ["Low-end operating point", "High-end operating point"]):
        d, io = vo/Vin, vo/R
        dil = vo*(1-d)/(L*fs)
        # Steady-state triangular inductor current, centered on Io.
        phase = np.mod(t, period)/period
        tri = np.where(phase < d, -dil/2 + (dil/d)*phase, dil/2 - (dil/(1-d))*(phase-d))
        il = io + tri
        # Capacitor voltage ripple from iC = iL - Io, integrated over each switching period.
        dt = t[1]-t[0]
        ic = il-io
        vraw = np.concatenate([[0.0], np.cumsum((ic[1:]+ic[:-1])*0.5*dt/C)])
        # Remove mean over full plotted interval to display vo(t)-Vo centered around zero.
        vr = (vraw - np.mean(vraw))*1000
        dvo = dil/(8*fs*C)
        axes[0].plot(t*1e6, il, color=color, label=f"{label}: ΔIL={dil:.4g} A p-p")
        axes[1].plot(t*1e6, vr, color=color, label=f"{label}: ideal ΔVo≈{dvo*1000:.4g} mV p-p")
    axes[0].set_title("Buck Converter Inductor Current and Output Ripple")
    axes[0].set_ylabel("Inductor current iL (A)")
    axes[1].set_ylabel("Output ripple vo(t) − Vo (mV)")
    axes[1].set_xlabel("Time (µs)")
    axes[0].grid(True, alpha=.3); axes[1].grid(True, alpha=.3)
    axes[0].legend(fontsize=8); axes[1].legend(fontsize=8)
    path=os.path.join(outdir, "buck_waveforms.png")
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="JSON file containing validated SI-unit inputs")
    ap.add_argument("--output-dir", default="output")
    args=ap.parse_args()
    try:
        with open(args.input, encoding="utf-8") as f:
            data=json.load(f)
        vmin,vmax=validate(data)
        result=design(data,vmin,vmax)
        plot=make_plot(data,result,vmin,vmax,args.output_dir)
        print(json.dumps({"status":"ok","inputs":data,"interpreted":{"Vo_min_V":vmin,"Vo_max_V":vmax},
            "L_H":result["L_H"],"C_F":result["C_F"],"worst_L_Vo_V":result["worst_L_Vo"],
            "worst_C_Vo_V":result["worst_C_Vo"],"points":result["points"],"plot":plot,
            "assumptions":["ideal switch, diode, and inductor","steady state","CCM","capacitor ESR/ESL ignored"]},indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

if __name__=="__main__":
    main()
