# ResiManage UX benchmark — 2026-10-17

## Purpose

Use established graduate-medical-education (GME), residency, and clinical scheduling products as workflow references, not as templates to copy. ResiManage must stay focused on CHU Nedir Mohamed's four-period rotation allocation, mandatory-versus-optional terrains, resident profiles, exam progression, DEMS decisions, Arabic/French/English, and mobile use.

## Ten comparable applications/platforms reviewed

1. **MedHub** — residency management, rotation/call/clinic schedules, absence workflows, curriculum objectives, learner portfolios, reporting.
2. **New Innovations** — resident records, rotation and daily schedules, evaluations, case/procedure logs, onboarding, accreditation, mobile access.
3. **Medtrics** — clinical schedule configuration, blocks, assignments, conflict/capacity visibility, evaluation workflows and analytics.
4. **MedHive** — resident portal, block rotation planning, call scheduling, leave requests, conferences and calendar export.
5. **Thalamus Core** — centralized calendar, flexible scheduling, waitlists, itinerary building, program-level reporting.
6. **MyEvaluations** — schedules/compliance, resident portfolios, competency milestones, learning assignments, evaluations and performance dashboards.
7. **Amion** — online hospital/residency schedules, availability and rule checks, schedule updates, mobile access and reporting.
8. **QGenda Advanced Scheduling** — rule-based schedule optimization, cross-department visibility, mobile access, change notifications and fairness controls.
9. **ACGME Cloud / Resident-Fellow Portal** — unified navigation, smart search, profile information, training history and milestone views.
10. **AAMC ERAS + Thalamus suite (Cortex, Core, Cerebellum, Itinerary Wizard)** — centralized applicant/program workflows, scheduling, scoring/ranking and analytics.

## Ten website resources reviewed

1. MedHub residency management: https://www.medhub.com/software/residency-management-software/
2. MedHub education management: https://www.medhub.com/software/
3. New Innovations: https://www.new-innov.com/pub/
4. QGenda residency management: https://www.qgenda.com/residency-management/
5. Medtrics platform: https://www.medtricslab.com/
6. Medtrics schedule optimization: https://www.medtricslab.com/solutions/schedule-optimization
7. MedHive: https://www.medhiive.com/
8. Thalamus Core: https://www.thalamusgme.com/thalamus-core
9. MyEvaluations features: https://www.myevaluations.com/features/
10. Amion: https://www.amion.com/home
11. ACGME Cloud experience update: https://www.acgme.org/newsroom/2026/4/new-acgme-cloud-updates-launching-april-13/
12. Stanford GME's MedHub overview: https://www.med.stanford.edu/gme/program_portal/medhub.html
13. SUNY Downstate's New Innovations overview: https://www.downstate.edu/education-training/graduate-medical-education/new-innovations.html
14. AAMC–Thalamus collaboration: https://www.aamc.org/services/eras-institutions/aamc-thalamus-strategic-collaboration

## UX patterns to adopt

- **Role-aware dashboard:** show only actions the current role can actually perform; keep read-only information available to standard users.
- **Short, grouped navigation:** organize daily work (Residents, Rotations, Capacity, History) separately from governance (Exams, Promotions, DEMS, Users, Audit, Backup/Restore). Keep the main action easy to find on a phone.
- **At-a-glance state:** show year, active/inactive status, rotation completion, capacity remaining, pending decisions and conflicts with both a label and a color/icon; never use color alone.
- **Resident profile as a coherent record:** clear photo/avatar, identity and contact details, year/status chips, rotation progress, exam results, objectives, full history and links to related decisions. Make photo replacement explicit and preview it before saving.
- **Calendar/block-first allocation:** make the four official periods visible, group by study year, emphasize year-4 → year-3 → year-2 → year-1 priority, and show capacity/conflicts before confirmation.
- **Safe, explainable actions:** preview imports before commit; explain validation errors beside the relevant field; confirm destructive operations; show a success/error message and retain an audit trail.
- **Mobile-first ergonomics:** touch targets around 44 px, no clipped controls, readable spacing, tables that scroll within their own panel, responsive form grids and clear save/cancel actions.
- **Multilingual/RTL quality:** preserve the same information hierarchy in Arabic RTL and French/English LTR; use logical CSS properties such as margin-inline-start; keep names, numbers and dates legible.
- **Accessible polish:** strong contrast, visible keyboard focus, semantic labels, reduced-motion support, consistent status chips, and no motion required to understand state.
- **Avoid unnecessary complexity:** no dense animated charts or too many accent colors on operational screens. Use calm navy/blue with restrained cyan/teal accents; reserve warm colors for warnings or attention states.

## Implementation status

- This candidate adds a structured resident-profile header, responsive identity fields, explicit image picker guidance, a client-side preview, mobile styling and visible focus states.
- The photo upload handler now validates actual image decoding, normalizes orientation/size, uses unique filenames and atomic writes, and preserves the current photo unless a valid replacement is uploaded.
- This is an initial profile-focused UX improvement, not a claim that every screen has completed the redesign. The full navigation/dashboard redesign and real Android file-picker behavior remain separate verification tasks.
- Candidate branch: resimanage-1-photo-ui-candidate, based on resimanage-1-backup. Do not merge into the backup. Run automated CI first; port only verified changes to resimanage-2-work.
