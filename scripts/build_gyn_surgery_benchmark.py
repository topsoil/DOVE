"""Build the 100-item synthetic gynecologic surgical-note extraction benchmark."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "benchmarks" / "gyn_surgical_note_extraction_100.json"
SOURCE = "prompts/gyn_surgical_note_feature_extraction.md"


@dataclass(frozen=True)
class Case:
    subdomain: str
    task: str
    note: str
    answer: str
    explanation: str
    difficulty: str = "intermediate"


CASES: list[Case] = []

def add(subdomain: str, task: str, note: str, answer: str,
        explanation: str, difficulty: str = "intermediate") -> None:
    CASES.append(Case(subdomain, task, note, answer, explanation, difficulty))


# 1. Actual gynecologic surgical involvement (12)
T = "Did the actual procedure involve an ovary, fallopian tube, uterus, cervix, or pelvic/abdominal peritoneum?"
add("Gynecologic surgical involvement", T, "A right salpingo-oophorectomy was completed; the adnexa was placed in a retrieval bag and sent to pathology.", "yes", "A fallopian tube and ovary were actually removed.", "basic")
add("Gynecologic surgical involvement", T, "Preoperative diagnosis: ovarian carcinoma. The operative report documents only an open appendectomy for acute appendicitis; the pelvis was not entered and no gynecologic procedure was performed.", "no", "The diagnosis alone is insufficient, and the documented appendectomy did not involve a listed gynecologic organ or pelvic/abdominal peritoneal cancer procedure.", "advanced")
add("Gynecologic surgical involvement", T, "The uterus, cervix, both tubes, and ovaries were removed en bloc after ligation of the uterine vessels.", "yes", "The completed hysterectomy and bilateral salpingo-oophorectomy involved several gynecologic organs.", "basic")
add("Gynecologic surgical involvement", T, "After abdominal entry, pelvic washings and biopsies of the cul-de-sac and right pelvic peritoneum were obtained.", "yes", "Pelvic peritoneal tissue was biopsied during the operation.")
add("Gynecologic surgical involvement", T, "Indication: adnexal mass. Cystoscopy with bilateral ureteral stent placement was performed; the gynecologic procedure was cancelled before abdominal entry.", "no", "Only urinary-tract procedures were performed; planned gynecologic surgery did not occur.", "advanced")
add("Gynecologic surgical involvement", T, "The available note states only, 'procedure performed as planned; specimens submitted.' The procedure name and specimen sites are absent.", "unsure", "The excerpt does not identify whether a gynecologic organ or peritoneum was involved.", "advanced")
add("Gynecologic surgical involvement", T, "A left salpingectomy was carried out for a torsed hydrosalpinx; the ovary was preserved.", "yes", "Removal of the fallopian tube constitutes gynecologic involvement.", "basic")
add("Gynecologic surgical involvement", T, "General surgery lysed small-bowel adhesions adjacent to the left ovary. The ovary and pelvic peritoneum were inspected but not biopsied, resected, or repaired.", "no", "Inspection and nearby adhesiolysis without a procedure on the listed organs or peritoneal tissue do not confirm involvement.", "advanced")
add("Gynecologic surgical involvement", T, "Three implants were excised from the anterior pelvic peritoneum for frozen section.", "yes", "The operation included resection of pelvic peritoneal tissue.")
add("Gynecologic surgical involvement", T, "The booking listed possible bilateral oophorectomy. At surgery, only an incisional hernia repair was completed; the pelvis was not entered.", "no", "A planned procedure is not evidence that it was performed.")
add("Gynecologic surgical involvement", T, "Repair of a dehisced vaginal cuff included reapproximation of the cuff to the residual cervical stroma.", "yes", "The repair involved cervical gynecologic tissue.")
add("Gynecologic surgical involvement", T, "The surgeon records a 'pelvic procedure' but supplies no procedure name, operative steps, or specimen description.", "unsure", "The wording is too nonspecific to confirm involvement of a listed structure.", "advanced")

# 2. Laparoscopic or robotic initiation (12)
T = "Was the operation performed with, or begun using, a laparoscopic, robotic, or other minimally invasive abdominal approach?"
add("Laparoscopic approach", T, "Pneumoperitoneum was established and four robotic ports were placed. The robotic hysterectomy proceeded without conversion.", "yes", "Robotic port placement confirms a minimally invasive approach.", "basic")
add("Laparoscopic approach", T, "The case began robotically with pelvic survey. Dense adhesions prevented safe progress, so the ports were removed and a midline laparotomy was made.", "yes", "A minimally invasive approach was initiated even though the case converted to open.", "advanced")
add("Laparoscopic approach", T, "A vertical midline incision was made from the pubis to above the umbilicus, and exploration proceeded by laparotomy.", "no", "Only an open approach is documented.", "basic")
add("Laparoscopic approach", T, "Although laparoscopy had been planned, the team elected before incision to proceed directly through a midline laparotomy; no ports were inserted.", "no", "Planning laparoscopy does not count when minimally invasive access never began.")
add("Laparoscopic approach", T, "A 5-mm optical trocar was introduced at Palmer's point, followed by two lower-quadrant ports.", "yes", "Trocar and port placement confirm laparoscopic access.")
add("Laparoscopic approach", T, "A hand-assisted laparoscopic approach was used for mobilization before specimen delivery through a small extraction incision.", "yes", "Hand-assisted laparoscopy remains a minimally invasive initiation.")
add("Laparoscopic approach", T, "A cystoscope was passed through the urethra to assess ureteral efflux. The abdominal operation itself was performed through an open incision.", "no", "Cystoscopy is not a laparoscopic or robotic abdominal approach.", "advanced")
add("Laparoscopic approach", T, "Diagnostic laparoscopy was initiated with an umbilical port but stopped after diffuse unresectable disease was seen.", "yes", "The operation began laparoscopically even though it was stopped.")
add("Laparoscopic approach", T, "Exploratory laparotomy and open omentectomy were performed. No scope, trocar, port, robotic, or minimally invasive technique is described.", "no", "The documented approach is open.")
add("Laparoscopic approach", T, "A laparoscopic survey was completed before conversion to a xiphoid-to-pubis incision for cytoreduction.", "yes", "The laparoscopic survey establishes minimally invasive initiation.")
add("Laparoscopic approach", T, "The operative report identifies a 'minimally invasive total hysterectomy' with robotic docking and bedside assistant ports.", "yes", "The note explicitly documents minimally invasive robotic surgery.", "basic")
add("Laparoscopic approach", T, "The procedure list names hysterectomy and staging, but the operative approach and access technique are not documented.", "unsure", "There is no evidence establishing open or minimally invasive access.", "advanced")

# 3. Extensive cytoreduction or debulking (11)
T = "Was this a full or extensive operation intended for cytoreduction, debulking, or interval debulking?"
add("Extensive cytoreduction", T, "The operation is titled 'primary cytoreductive surgery' and included hysterectomy, bilateral salpingo-oophorectomy, omentectomy, and pelvic peritonectomy.", "yes", "The intent and multi-site procedures establish extensive cytoreduction.", "basic")
add("Extensive cytoreduction", T, "After neoadjuvant chemotherapy, interval debulking included infragastric omentectomy and stripping of bilateral diaphragmatic and pelvic peritoneum.", "yes", "Interval debulking with omentectomy and peritoneal stripping is extensive cytoreduction.")
add("Extensive cytoreduction", T, "A bilateral salpingo-oophorectomy was completed for an isolated adnexal mass; no omentectomy, peritoneal resection, or debulking intent was documented.", "no", "Adnexal removal alone does not establish a full cytoreductive operation.")
add("Extensive cytoreduction", T, "Diagnostic laparoscopy with two peritoneal biopsies was performed to assess resectability, and no tumor was removed beyond the biopsies.", "no", "A diagnostic assessment is not extensive cytoreduction.")
add("Extensive cytoreduction", T, "Tumor debulking required omentectomy, rectosigmoid resection, splenectomy, and excision of diaphragmatic implants.", "yes", "The explicit debulking intent and multiple upper and lower abdominal resections indicate extensive surgery.")
add("Extensive cytoreduction", T, "The heading states 'possible debulking.' The body is truncated after abdominal entry and does not list completed resections.", "unsure", "Planned or possible debulking without operative details cannot confirm an extensive completed attempt.", "advanced")
add("Extensive cytoreduction", T, "A staging omentectomy and pelvic washings were performed after removal of a confined ovarian tumor; no cytoreduction or gross peritoneal disease was described.", "no", "Staging omentectomy alone is not described as full or extensive cytoreduction.", "advanced")
add("Extensive cytoreduction", T, "Complete gross resection was pursued with total omentectomy, right diaphragm peritonectomy, porta hepatis nodule excision, and small-bowel mesenteric implant resection.", "yes", "The stated goal and multi-region resections support extensive cytoreduction.")
add("Extensive cytoreduction", T, "Fertility-sparing ovarian cystectomy was performed, with preservation of the uterus and contralateral adnexa.", "no", "A limited cystectomy is not an extensive debulking operation.", "basic")
add("Extensive cytoreduction", T, "The surgeon documents 'optimal cytoreduction' after hysterectomy, omentectomy, pelvic peritonectomy, and resection of paracolic-gutter implants.", "yes", "Explicit cytoreduction plus extensive multi-site resection meets the definition.")
add("Extensive cytoreduction", T, "Hysterectomy, bilateral salpingo-oophorectomy, and sentinel pelvic-node mapping were completed for apparent uterine-confined disease.", "no", "This staging operation lacks debulking intent or extensive peritoneal resection.")

# 4. Closed or aborted before planned completion (11)
T = "Was the planned therapeutic operation closed or aborted early?"
add("Surgery aborted early", T, "Diffuse tumor encased the mesenteric root and porta hepatis. The planned debulking was abandoned as unresectable after biopsies, and the abdomen was closed.", "yes", "The note explicitly says the planned debulking was abandoned because disease was unresectable.", "basic")
add("Surgery aborted early", T, "Exploratory laparotomy resulted in an open-and-close procedure; no planned resection was attempted because of frozen pelvis and extensive carcinomatosis.", "yes", "An open-and-close operation due to disease extent is an early abort.")
add("Surgery aborted early", T, "Hysterectomy, omentectomy, and all planned peritoneal resections were completed. Hemostasis was confirmed and the procedure was then concluded.", "no", "'Concluded' describes the normal end of a completed operation.", "advanced")
add("Surgery aborted early", T, "After completion of the planned bilateral salpingo-oophorectomy, counts were correct and the operation was terminated without complication.", "no", "'Terminated' follows documented completion and does not mean aborted.", "advanced")
add("Surgery aborted early", T, "During initial dissection the patient developed refractory hypotension. The resection was stopped, packing was placed, and the planned cytoreduction was not completed.", "yes", "The operation stopped early because of instability and the planned procedure was not completed.")
add("Surgery aborted early", T, "The intent changed from cytoreduction to biopsy only after unresectable small-bowel mesenteric disease was identified.", "yes", "Conversion from therapeutic intent to biopsy only indicates early abandonment of the planned treatment.")
add("Surgery aborted early", T, "The robotic case converted to open for adhesions, after which the hysterectomy, omentectomy, and planned tumor resections were completed.", "no", "Conversion of approach is not abortion when the planned procedure is completed.")
add("Surgery aborted early", T, "Only a peritoneal biopsy was performed. The excerpt does not state the planned procedure or why no additional surgery occurred.", "unsure", "Without the plan or a statement of abandonment, early abortion cannot be determined.", "advanced")
add("Surgery aborted early", T, "All planned cytoreductive steps were performed, although one implant densely adherent to the vena cava was intentionally left in place.", "no", "Residual disease does not by itself mean the operation was aborted early.", "advanced")
add("Surgery aborted early", T, "Before the planned hysterectomy could begin, severe bronchospasm prompted the surgeon and anesthesiologist to abort the case and close the port sites.", "yes", "The note explicitly states that the case was aborted before the planned procedure.")
add("Surgery aborted early", T, "The planned procedure was diagnostic laparoscopy with biopsies only. The survey and biopsies were completed, and the ports were closed.", "no", "A limited diagnostic plan was completed as intended.")

# 5. Residual disease after cytoreduction (12)
T = "What residual-disease category should be assigned at the end of this operation?"
add("Residual disease", T, "Following cytoreduction, no visible tumor remained in the abdomen or pelvis; the surgeon records complete gross resection.", "R0", "No visible residual disease is R0.", "basic")
add("Residual disease", T, "At completion, scattered implants measuring up to 3 mm remained on the small-bowel serosa.", "R0.5", "Residual nodules under 5 mm are classified R0.5.")
add("Residual disease", T, "The largest residual implant was 8 mm at the mesenteric root.", "R1", "Residual disease from 5 through 10 mm is R1.")
add("Residual disease", T, "A 2-cm plaque remained at the porta hepatis after debulking.", "R2", "Residual disease greater than 10 mm is R2.")
add("Residual disease", T, "The surgeon states that residual tumor remained but gives no measurement or size descriptor.", "unspecified", "Residual disease is present, but its size is not specified.")
add("Residual disease", T, "A diagnostic ovarian cystectomy was completed. The note does not describe cytoreduction or residual tumor.", "not_mentioned", "This was not a debulking operation and no residual status was documented.")
add("Residual disease", T, "Residual implants measured 4 mm on the diaphragm and 1.5 cm at the splenic hilum.", "R2", "The worst documented residual is 1.5 cm, which is greater than 10 mm.", "advanced")
add("Residual disease", T, "A single 6-mm mesenteric nodule could not be removed; all other visible disease was resected.", "R1", "Six millimeters falls in the 5–10 mm R1 category.")
add("Residual disease", T, "The largest visible residual focus was 0.4 cm on the right hemidiaphragm.", "R0.5", "0.4 cm equals 4 mm, which is under 5 mm.")
add("Residual disease", T, "At the end of the case, residual tumor measured 1.0 cm along the lesser curvature.", "R1", "One centimeter equals 10 mm, within the R1 range.")
add("Residual disease", T, "A 1.1-cm implant remained around the celiac axis.", "R2", "1.1 cm equals 11 mm and is therefore R2.")
add("Residual disease", T, "Miliary residual implants, all less than 3 mm, remained over the bowel mesentery.", "R0.5", "The documented residual foci are under 5 mm.")

# 6. Intraoperative disease burden (11)
T = "What is the most extensive intraoperative disease-burden category?"
add("Disease burden", T, "Tumor involved both ovaries and the cul-de-sac. The omentum, diaphragms, liver surface, and upper abdomen were free of disease.", "pelvic_disease", "The documented disease is confined to pelvic structures.", "basic")
add("Disease burden", T, "Omental caking and implants along both paracolic gutters were present, with no diaphragmatic, hepatic, splenic, gastric, or lesser-sac disease.", "lower_abdominal_disease", "Omental and lower-abdominal involvement without upper-abdominal sites is lower abdominal disease.")
add("Disease burden", T, "Multiple implants covered the right hemidiaphragm and liver capsule.", "upper_abdominal_disease", "Diaphragm and liver-surface involvement is upper abdominal disease.")
add("Disease burden", T, "The abdomen and pelvis showed diffuse miliary studding, each focus under 5 mm, without bulky masses.", "miliary_disease", "Diffuse subcentimeter studding without bulky disease fits the miliary category.")
add("Disease burden", T, "The operative report lists the procedures but gives no description of tumor distribution at exploration.", "not_mentioned", "Disease extent or distribution is not documented.")
add("Disease burden", T, "A bulky pelvic mass was present together with tumor nodules on the left diaphragm.", "upper_abdominal_disease", "The highest documented distribution includes the diaphragm, an upper-abdominal site.", "advanced")
add("Disease burden", T, "Tumor involved the pelvis, infracolic omentum, and lower paracolic gutters; the supracolic abdomen was normal.", "lower_abdominal_disease", "Disease extends into the lower abdomen but spares upper-abdominal structures.")
add("Disease burden", T, "A 1-cm implant was identified at the porta hepatis, with additional pelvic disease.", "upper_abdominal_disease", "Porta hepatis involvement assigns the upper-abdominal category.")
add("Disease burden", T, "Countless 2- to 4-mm implants diffusely studded the peritoneum from pelvis to upper abdomen, with no dominant bulky lesion.", "miliary_disease", "Diffuse small-volume peritoneal studding without bulky disease is miliary.")
add("Disease burden", T, "An adnexal tumor and bulky pelvic and paraaortic nodes were found; the omentum and upper abdomen were negative.", "pelvic_disease", "The definition permits adnexal disease with bulky pelvic or paraaortic nodes.")
add("Disease burden", T, "A 4-cm omental cake and multiple pelvic implants were seen, but the diaphragm, liver, stomach, spleen, pancreas, and lesser sac were uninvolved.", "lower_abdominal_disease", "Bulky omental disease without upper-abdominal involvement is lower abdominal rather than miliary disease.", "advanced")

# 7. Estimated blood loss (11)
T = "What estimated blood loss should be recorded in cc?"
add("Estimated blood loss", T, "Estimated blood loss was 250 mL.", "250", "mL and cc are equivalent, so the value is 250 cc.", "basic")
add("Estimated blood loss", T, "EBL: 1.5 L.", "1500", "1.5 liters converts to 1500 cc.")
add("Estimated blood loss", T, "Blood loss was minimal.", "0", "The specification maps 'minimal' to 0 cc.")
add("Estimated blood loss", T, "EBL was less than 50 cc.", "50", "The specification maps '<50' to 50 cc.", "advanced")
add("Estimated blood loss", T, "Fluids and urine output are documented, but estimated blood loss is not listed.", "-1", "Absent EBL documentation is encoded as -1.")
add("Estimated blood loss", T, "Estimated blood loss: 75 cc.", "75", "The documented numeric EBL is 75 cc.", "basic")
add("Estimated blood loss", T, "The anesthesia record and operative note agree on an EBL of 0.8 L.", "800", "0.8 liters converts to 800 cc.")
add("Estimated blood loss", T, "EBL was 1200 mL after completion of the bowel resection.", "1200", "The value is already in mL, equivalent to 1200 cc.")
add("Estimated blood loss", T, "The surgeon described negligible blood loss.", "0", "The specification maps 'negligible' to 0 cc.")
add("Estimated blood loss", T, "The note states, 'blood loss not recorded.'", "-1", "An explicitly unrecorded value is treated as not mentioned and encoded -1.")
add("Estimated blood loss", T, "Approximately 400 cc of blood loss was estimated for the case.", "400", "The documented estimate is 400 cc.")

# 8. Hemostasis at completion (10)
T = "Was satisfactory hemostasis documented at the end of surgery?"
add("Hemostasis", T, "The pelvis was irrigated, and hemostasis was achieved before fascial closure.", "yes", "The note explicitly states that hemostasis was achieved.", "basic")
add("Hemostasis", T, "After lowering insufflation pressure, all pedicles were inspected and hemostasis was satisfactory.", "yes", "Satisfactory hemostasis is explicitly documented.")
add("Hemostasis", T, "All bleeding points were controlled with cautery and suture; the operative field was dry.", "yes", "Control of all bleeding and a dry field establish satisfactory hemostasis.")
add("Hemostasis", T, "Diffuse pelvic oozing persisted despite cautery, and the patient left the operating room with packing in place for ongoing hemorrhage control.", "no", "Persistent uncontrolled oozing indicates hemostasis was not achieved.")
add("Hemostasis", T, "Counts were correct and the incision was closed in layers. No statement addresses bleeding control or hemostasis.", "not_mentioned", "Closure and correct counts do not themselves document hemostasis.", "advanced")
add("Hemostasis", T, "The surgeon explicitly documented that adequate hemostasis could not be obtained before transfer to interventional radiology.", "no", "The note explicitly states that hemostasis was not obtained.")
add("Hemostasis", T, "A small venous bleeder was ligated; repeat inspection confirmed good hemostasis.", "yes", "Good hemostasis was confirmed after treatment.")
add("Hemostasis", T, "The specimen was removed and the port sites were closed. Hemostasis is not discussed.", "not_mentioned", "The note contains no bleeding-control assessment.")
add("Hemostasis", T, "The pelvis was packed because brisk bleeding continued from the presacral space.", "no", "Continued brisk bleeding requiring packing indicates lack of satisfactory hemostasis.")
add("Hemostasis", T, "Final inspection under reduced pneumoperitoneum showed a dry field with no active bleeding.", "yes", "A dry field with no active bleeding documents satisfactory hemostasis.")

# 9. Wound classification (10)
T = "What wound classification should be assigned?"
add("Wound classification", T, "Wound classification: Class I (clean). No hollow viscus was entered.", "ClassI", "The explicit Class I designation controls.", "basic")
add("Wound classification", T, "The operative note records wound class II, clean-contaminated.", "ClassII", "The explicit Class II designation controls.", "basic")
add("Wound classification", T, "A planned rectosigmoid resection was completed with controlled bowel entry and no spillage.", "ClassII", "Controlled GI-tract entry without unusual contamination is Class II.")
add("Wound classification", T, "During enterotomy repair, gross fecal spillage contaminated the operative field; no explicit class was recorded.", "ClassIII", "Gross GI spillage without an explicit class supports Class III.")
add("Wound classification", T, "A pelvic abscess containing frank pus was encountered and drained.", "ClassIV", "Existing purulent infection is Class IV.")
add("Wound classification", T, "The report contains no wound class and no description of tract entry, contamination, infection, or spillage.", "not_mentioned", "There is insufficient documentation to assign a wound class.")
add("Wound classification", T, "The surgeon explicitly labels the case Class II. A small amount of enteric fluid was suctioned immediately during the controlled anastomosis.", "ClassII", "The specification directs use of the explicit classification when one is documented.", "advanced")
add("Wound classification", T, "A previously perforated sigmoid tumor with purulent peritonitis was resected; no explicit wound class appears.", "ClassIV", "A perforated viscus with established purulent infection is Class IV.")
add("Wound classification", T, "A major break in sterile technique occurred when a nonsterile instrument contacted the open field; the case was not explicitly classified.", "ClassIII", "A major sterile-technique break supports Class III.")
add("Wound classification", T, "The bladder was intentionally opened and repaired under controlled conditions without infection or spillage; no explicit class was stated.", "ClassII", "Controlled GU-tract entry is clean-contaminated, Class II.")


VALUES = {
    "Gynecologic surgical involvement": ["yes", "no", "unsure"],
    "Laparoscopic approach": ["yes", "no", "unsure"],
    "Extensive cytoreduction": ["yes", "no", "unsure"],
    "Surgery aborted early": ["yes", "no", "unsure"],
    "Residual disease": ["R0", "R0.5", "R1", "R2", "unspecified", "not_mentioned"],
    "Disease burden": ["pelvic_disease", "lower_abdominal_disease", "upper_abdominal_disease", "miliary_disease", "not_mentioned"],
    "Hemostasis": ["yes", "no", "not_mentioned"],
    "Wound classification": ["ClassI", "ClassII", "ClassIII", "ClassIV", "not_mentioned"],
}
EBL_POOL = ["-1", "0", "50", "75", "100", "250", "400", "800", "1200", "1500"]


def options_for(case: Case, index: int) -> tuple[dict[str, str], str]:
    if case.subdomain == "Estimated blood loss":
        distractors = [v for v in EBL_POOL if v != case.answer]
        start = (index * 3) % len(distractors)
        values = [case.answer] + [distractors[(start + j) % len(distractors)] for j in range(3)]
    else:
        values = [case.answer] + [v for v in VALUES[case.subdomain] if v != case.answer]
    shift = (index - 1) % len(values)
    values = values[shift:] + values[:shift]
    options = dict(zip("ABCDEF", values))
    correct = next(label for label, value in options.items() if value == case.answer)
    return options, correct


def build() -> list[dict]:
    assert len(CASES) == 100, f"Expected 100 cases, got {len(CASES)}"
    items = []
    for index, case in enumerate(CASES, 1):
        options, correct = options_for(case, index)
        items.append({
            "id": f"gyn_surg_{index:03d}",
            "domain": "gynecologic_surgical_note_extraction",
            "subdomain": case.subdomain,
            "question_type": "single_choice",
            "question": (
                "Synthetic operative-note excerpt:\n"
                f"\"{case.note}\"\n\n"
                f"Extraction task: {case.task}"
            ),
            "options": options,
            "correct_answer": correct,
            "correct_answers": None,
            "explanation": case.explanation,
            "difficulty": case.difficulty,
            "tags": ["clinical_nlp", "synthetic_note", "gynecologic_surgery",
                     case.subdomain.lower().replace(" ", "_")],
            "source": SOURCE,
            "review_status": "llm_generated",
            "version": "0.1",
            "provenance": {
                "source_specification": SOURCE,
                "authoring_method": "Synthetic cases authored from the user-supplied extraction specification",
                "synthetic": True,
                "contains_patient_data": False,
                "human_review_required": True,
                "intended_use": "Evaluate clinical-curation extraction behavior; not clinical decision support",
            },
        })
    return items


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = build()
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(data)} items to {OUT}")
