# PETi hackathon demo script (about four minutes)

Record in English or add accurate English subtitles. Keep the main agent execution unedited and show the result as it arrives.

1. **Problem and value (0:00–0:30).** Explain that pet owners often have fragmented observations and need a cautious, evidence-linked next step rather than an unsafe diagnosis.
2. **Two-pet demo (0:30–1:10).** Open `https://peti-care.web.app/?demo=1`, select Luna (healthy) and Max (needs observation), and show the five synthetic evidence images for each. Explain that the images are synthetic demo fixtures.
3. **Agent workspace (1:10–2:30).** Open Agents, select a pet and start “Review recent evidence”. Show the run identifier, asynchronous progress and the stages: orchestrator, evidence intake, specialist and safety review. Do not skip or fake the run.
4. **Safety outcome (2:30–3:05).** Show the evidence-linked, non-diagnostic report and the review-required behavior for uncertain findings.
5. **Cloud proof (3:05–3:35).** Show the Cloud Run API and private worker services, Cloud Tasks delivery and Firestore run state or logs. Keep secrets, tokens and personal data hidden.
6. **Architecture and close (3:35–4:00).** Show the architecture diagram and state the stack: Gemini 3.5, Google ADK, Cloud Run, Firestore, Storage and Cloud Tasks.

Never claim that synthetic demo images are real clinical data. Use a disposable judge account if authentication is shown, and revoke it after recording.
