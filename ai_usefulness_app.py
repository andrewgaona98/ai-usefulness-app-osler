import streamlit as st

st.set_page_config(page_title="AI Usefulness Checker", layout="centered")

st.title("🩺💡 Should I Use AI For This Clinical Question? (v2 – Stronger Heuristics)")

st.markdown(
    """
Paste your **clinical question** (no PHI) and this tool will estimate an
**AI usefulness score (0–10)** based on multiple dimensions:

- ⏱️ Time urgency  
- ⚠️ Risk of acting on bad info  
- 🏥 Dependence on local protocols  
- 📚 Evidence / literature orientation  
- 🎓 Educational / explanation focus  

> ⚠️ This is an **educational heuristic**, not clinical decision support.
> Always follow your training, local protocols, seniors, and attendings.
"""
)

question = st.text_area(
    "Clinical question (no patient identifiers):",
    height=200,
    placeholder=(
        "e.g. In a 70-year-old with new AF and CKD3, what does the evidence say "
        "about DOAC vs warfarin for stroke prevention?"
    ),
)

def analyze_dimensions(text: str):
    """
    Analyze the question along 5 dimensions:
    - time_urgency (0–2, higher = less urgent)
    - risk_level (0–2, higher = safer to experiment)
    - protocol_independence (0–2)
    - evidence_orientation (0–2)
    - educational_frame (0–2)
    Also returns a list of reasoning strings and a hard_stop flag.
    """

    t = text.lower()
    reasons = []
    hard_stop = False

    # ---------- 1. TIME URGENCY ----------
    time_urgency = 2  # default: low urgency unless we see otherwise
    time_critical_terms = [
        "code blue", "cardiac arrest", "pulseless", "pea", "vfib", "v-fib",
        "vtach", "v-tach", "rapid response", "rrt", "stat", "immediately",
        "right now", "need to decide now", "crashing", "severe hypotension",
        "shock", "tpa", "t-pa", "alteplase", "stroke code", "activate stroke",
        "massive bleed", "massive hemor", "massive hemorrhage", "intubate now",
        "emergent intubation", "emergent cath", "stemi activation"
    ]
    if any(term in t for term in time_critical_terms):
        time_urgency = 0
        reasons.append("Detected **time-critical / crashing context** → urgency set to HIGH.")
        hard_stop = True
    else:
        # mildly urgent language
        medium_urgency_terms = ["today", "within the hour", "this hour", "soon", "acutely"]
        if any(term in t for term in medium_urgency_terms):
            time_urgency = 1
            reasons.append("Detected **some time pressure** → urgency set to MODERATE.")
        else:
            reasons.append("No strong urgency language → urgency set to LOW.")

    # ---------- 2. RISK LEVEL ----------
    # Start at moderate, then adjust
    risk_level = 1
    high_risk_terms = [
        "tpa", "thrombolysis", "thrombolytics", "alteplase",
        "push dose", "push-dose", "bolus pressor", "pressors", "vasopressor",
        "levophed", "norepinephrine", "epinephrine", "dopamine", "dobutamine",
        "amiodarone bolus", "lidocaine bolus", "chemo", "chemotherapy",
        "intubate", "extubate", "ecmo", "lvad", "vent settings", "crrt",
        "dialysis initiation", "emergent surgery"
    ]
    if any(term in t for term in high_risk_terms):
        risk_level = 0
        reasons.append("Detected **high-stakes intervention language** → risk level set to HIGH.")
        hard_stop = True
    else:
        low_risk_terms = [
            "explain", "counsel", "board prep", "studying", "education", "for teaching",
            "for teaching purposes", "long-term management", "in general", "overall strategy"
        ]
        if any(term in t for term in low_risk_terms):
            risk_level = 2
            reasons.append("Detected **educational / low-risk framing** → risk level set to LOW.")
        else:
            reasons.append("No extreme risk terms detected → risk level set to MODERATE.")

    # ---------- 3. PROTOCOL DEPENDENCE ----------
    protocol_independence = 2  # assume fairly general unless we see protocol-ish words
    protocol_terms = [
        "hospital protocol", "institutional protocol", "order set", "orderset",
        "nomogram", "policy", "local protocol", "stroke protocol",
        "sepsis bundle", "vent weaning protocol", "insulin drip protocol",
        "heparin drip protocol", "dka protocol"
    ]
    if any(term in t for term in protocol_terms):
        protocol_independence = 0
        reasons.append("Detected **hospital-specific / protocol language** → protocol-independence set to LOW.")
    else:
        mixed_terms = ["our hospital", "at our institution", "formulary"]
        if any(term in t for term in mixed_terms):
            protocol_independence = 1
            reasons.append("Detected **some local context language** → protocol-independence set to MODERATE.")
        else:
            reasons.append("No protocol language → protocol-independence set to HIGH.")

    # ---------- 4. EVIDENCE ORIENTATION ----------
    evidence_orientation = 0
    evidence_terms = [
        "evidence", "literature", "trial", "trials", "rct", "randomized",
        "meta-analysis", "meta analysis", "systematic review", "cohort study",
        "compare", "comparison", "noninferior", "non-inferior",
        "superior", "mortality benefit", "outcomes of", "hazard ratio",
        "guideline", "guidelines", "class i recommendation", "class ii", "class 1",
        "aha", "acc", "esc", "chest guideline"
    ]
    if any(term in t for term in evidence_terms):
        # strongly evidence-oriented if multiple hits
        hit_count = sum(term in t for term in evidence_terms)
        if hit_count >= 2:
            evidence_orientation = 2
            reasons.append("Multiple **evidence/guideline cues** detected → evidence-orientation set to HIGH.")
        else:
            evidence_orientation = 1
            reasons.append("Some **evidence/guideline language** → evidence-orientation set to MODERATE.")
    else:
        reasons.append("No obvious evidence/guideline cues → evidence-orientation set to LOW.")

    # ---------- 5. EDUCATIONAL / EXPLANATION FRAME ----------
    educational_frame = 0
    teaching_terms = [
        "explain to a patient", "explain to patient", "how to explain",
        "how to counsel", "counseling", "patient-friendly", "plain language",
        "teach an intern", "teach a medical student", "for teaching", "for education",
        "board prep", "for studying", "moc", "simple explanation", "lay terms"
    ]
    if any(term in t for term in teaching_terms):
        educational_frame = 2
        reasons.append("Detected **teaching / patient-education focus** → educational-frame set to HIGH.")
    else:
        mild_edu_terms = ["understand the mechanism", "pathophysiology", "why does", "mechanism of"]
        if any(term in t for term in mild_edu_terms):
            educational_frame = 1
            reasons.append("Detected **mechanism / understanding focus** → educational-frame set to MODERATE.")
        else:
            reasons.append("No explicit educational framing → educational-frame set to LOW.")

    return {
        "time_urgency": time_urgency,
        "risk_level": risk_level,
        "protocol_independence": protocol_independence,
        "evidence_orientation": evidence_orientation,
        "educational_frame": educational_frame,
        "reasons": reasons,
        "hard_stop": hard_stop,
    }

def compute_ai_usefulness(dim):
    """
    Convert dimension scores into a 0–10 AI usefulness score.
    time_urgency: 0–2  (more time = better)
    risk_level: 0–2    (safer decisions = better)
    protocol_independence: 0–2
    evidence_orientation: 0–2
    educational_frame: 0–2
    """
    tu = dim["time_urgency"]
    rl = dim["risk_level"]
    pi = dim["protocol_independence"]
    eo = dim["evidence_orientation"]
    ef = dim["educational_frame"]

    # Hard stop: if hard_stop is flagged, cap max band
    # But still compute score so they see the breakdown.
    score = (
        (2 - tu) * 2   # more time → higher score
        + (rl) * 2     # higher risk_level value means lower real risk
        + (pi) * 2
        + (eo) * 2
        + (ef) * 1
    )

    # Normalize roughly into 0–10
    score = max(0, min(10, score))

    # If hard_stop, force it into lower band if it came out high
    if dim["hard_stop"] and score > 3:
        score = 3.0

    return score

if st.button("Calculate AI Usefulness Score") and question.strip():
    dim = analyze_dimensions(question)
    score = compute_ai_usefulness(dim)

    if score <= 3:
        label = "❌ AI not recommended as a starting point"
        color = "red"
        summary = (
            "This question likely involves **time-critical, high-risk, or protocol-driven decisions**. "
            "Prioritize **stabilizing the patient, using local protocols, and speaking with a senior/attending**. "
            "AI can still be used later for debriefing or education."
        )
    elif score <= 7:
        label = "⚠️ Use AI only as an adjunct (and verify)"
        color = "orange"
        summary = (
            "AI may be helpful for **finding evidence, exploring options, and clarifying mechanisms**, "
            "but you should **cross-check with guidelines/UpToDate and your team** before changing management."
        )
    else:
        label = "✅ Great use-case for AI as an information helper"
        color = "green"
        summary = (
            "This looks like a good situation to use AI for **literature synthesis, guideline summaries, and explanations**. "
            "Still treat outputs as **informational**, not as direct orders."
        )

    st.markdown(f"### AI Usefulness Score: **{score:.1f}/10**")
    st.markdown(f"**<span style='color:{color}'>{label}</span>**", unsafe_allow_html=True)
    st.markdown(summary)

    st.markdown("#### Dimension breakdown")
    dim_table = {
        "Dimension": [
            "Time urgency (0–2, higher = less urgent)",
            "Risk level (0–2, higher = safer to experiment)",
            "Protocol independence (0–2)",
            "Evidence orientation (0–2)",
            "Educational frame (0–2)",
        ],
        "Score": [
            dim["time_urgency"],
            dim["risk_level"],
            dim["protocol_independence"],
            dim["evidence_orientation"],
            dim["educational_frame"],
        ],
    }
    st.table(dim_table)

    with st.expander("Why did I get this score? (rules that fired)"):
        for r in dim["reasons"]:
            st.markdown(f"- {r}")

st.markdown("---")
st.caption(
    "This tool uses rule-based heuristics for educational purposes only. "
    "It does **not** understand full clinical context and is not clinical decision support."
)
