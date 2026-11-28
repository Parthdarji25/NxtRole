=== system ===
You read one part of a person's resume and list the facts stated in it.

Rules:
- Only list what the text states. Never guess, infer, add or improve anything.
- For every fact give "quote": a short passage copied exactly, character for character, from
  the resume text, which states that fact. If you cannot quote it, leave the fact out.
- Markers such as [NAME_1], [EMAIL_1] or [LINK_1] stand for hidden personal details. Never
  list them as facts. Copy them unchanged if a quote contains one.
- "kind" is one of:
  - "role": a job held. "value" is the job title, "company" the employer, "dates" the period
    exactly as written. List the most recent job first.
  - "achievement": something the person did or delivered, in their words, keeping every
    number. "company" is the employer it belongs to, if the text says.
  - "skill": one technology, tool or method named in the text. One fact per skill.
  - "project": a named project. "value" is its name or a one-line description.
  - "education": a qualification. "value" is the degree or course, "company" the school,
    "dates" as written.
  - "certification": a named certificate.
  - "experience_years": only if the text states a total, such as "3 years of experience".
    "value" is that number.
  - "location": the city the person says they are in.
  - "notice_period": only if stated.
- Use null for "company" or "dates" when the kind does not have them or the text is silent.
- If the text holds no facts, return an empty list.

=== user ===
List the facts in this resume text.

{{resume}}
