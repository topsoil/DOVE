# Gynecologic Oncology Surgical Note Feature Extraction

This benchmark specification is adapted from the user-supplied ovarian-cancer surgical-note extraction prompt. It defines nine curator targets:

1. **Gynecologic surgical involvement**: confirm an actual procedure on ovary, tube, uterus, cervix, or pelvic/abdominal peritoneum. Diagnosis or intent alone is insufficient. Values: `yes`, `no`, `unsure`.
2. **Laparoscopic approach**: count laparoscopic, robotic, trocar/port-based, or minimally invasive initiation as `yes`, including conversion to open. Values: `yes`, `no`, `unsure`.
3. **Extensive cytoreduction**: identify full/extensive cytoreduction, debulking, or interval debulking. Multi-site procedures such as omentectomy plus peritoneal resection support `yes`. Values: `yes`, `no`, `unsure`.
4. **Closed or aborted early**: use `yes` only when the planned therapeutic operation was abandoned or stopped early. Routine phrases such as “procedure concluded” after completion are `no`. Values: `yes`, `no`, `unsure`.
5. **Residual disease**: for cytoreduction, report the worst documented residual: `R0` (none), `R0.5` (<5 mm), `R1` (5–10 mm), `R2` (>10 mm), `unspecified`, or `not_mentioned`.
6. **Disease burden**: report the most extensive intraoperative distribution: `pelvic_disease`, `lower_abdominal_disease`, `upper_abdominal_disease`, `miliary_disease`, or `not_mentioned`.
7. **Estimated blood loss**: return cc/mL as an integer; liters are converted to cc. “Minimal/negligible” is 0, “<50” is 50, and absent documentation is -1.
8. **Hemostasis**: values are `yes`, `no`, or `not_mentioned`.
9. **Wound class**: explicit class takes priority. Otherwise infer `ClassI`, `ClassII`, `ClassIII`, `ClassIV`, or `not_mentioned` from contamination.

All operative-note excerpts in the benchmark are synthetic. They contain no patient identifiers and must not be treated as clinical documentation or clinical guidance.
