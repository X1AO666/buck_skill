# Approximation and independent verification

## What is approximated

The assignment equations use nearly constant output voltage during each period to obtain triangular inductor current. They then approximate load current as constant, so iC is the AC part of that assumed triangle. Integrating the triangle is analytic, but the resulting voltage is not an exact solution of the coupled L-C-R switching circuit.

The coupled ideal CCM equations are:

```text
diL/dt = (u Vin - v)/L, u=1 during ON, u=0 during OFF
dv/dt = (iL - v/R)/C
```

The capacitance must make its switching-frequency impedance small relative to load resistance for neglecting AC load current to be reasonable. See [ADI AN-1144, Estimating Output Ripple](https://www.analog.com/en/resources/app-notes/an-1144.html). Low relative output ripple alone also does not bound the error near dropout: ripple may be large relative to Vin-Vo, changing the inductor slope. CCM must be checked with the more complete solution when near its boundary.

## Screening, not guaranteed error bounds

The script retains the assignment's acceptance rule rv>0, rather than inventing a new invalid-input constraint. It emits structured JSON and stderr warnings if any project heuristic is exceeded:

- predicted voltage ripple >5% p-p of Vo;
- eta=1/(2 pi fsw C R)>0.1;
- predicted voltage ripple/min(Vo,Vin-Vo)>0.1 at an endpoint;
- requested rL>=1.8 (close to the approximate CCM boundary).

These thresholds are chosen for this project; they are not prescribed by ADI or TI, and passing them does not guarantee a particular physical accuracy or that exact ripple constraints hold. If warnings occur, report only provisional formula estimates and recommend independent validation. Never claim a successful script exit proves CCM or the limits in the physical circuit. Do not silently change the requested ripple to fit the model.

## Optional independent numerical comparison

Install the separate `requirements-validation.txt` dependencies in your chosen environment if unavailable. Run:

```text
python "<SKILL_DIR>/scripts/compare_switched.py" --input "<absolute-input.json>" --output-dir "<absolute-fresh-output-dir>"
```

The reference solver obtains the periodic state from ON/OFF affine matrix exponentials, then integrates the coupled ODE with SciPy DOP853 at two tolerances. Derivative roots locate current and voltage extrema. It reports periodic residuals, changes with tighter tolerance, predicted-versus-reference ripple differences, and whether requested ripple ratios are exceeded.

If the candidate valley current is nonpositive, the assumed two-state diode-buck CCM model is invalid. Such trajectories are labeled invalid CCM candidates; they are not a DCM solution and must not be used to claim diode-buck ripple compliance. The script does not auto-correct the selected components, simulate a control loop, or include losses, ESR/ESL or component tolerances. It is a numerical physics cross-check, not SPICE or hardware validation. Comparison endpoints do not prove full-range exact-model compliance.

## Extending to components

[TI's Buck power-stage guide](https://www.ti.com/lit/an/slva477b/slva477b.pdf) treats capacitor ESR and transient requirements separately. Real selection also needs nominal series values, tolerance and bias derating, inductor peak/RMS ratings, component loss, heat, and controller stability. This teaching skill does not implement those tasks.
