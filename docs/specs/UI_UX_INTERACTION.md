# PETi — Complete UI/UX & Interaction Specification

**Version:** 1.0.0-cloud  
**Date:** 2026-08-12  
**Status:** Canonical UI/UX implementation specification  
**Primary platform:** Native Android  
**Product scope:** Companion animals / pets  
**First certified AI species:** Dog  
**AI runtime:** Cloud-only  
**Commercial model:** Free-first; no ambient advertising; optional rewarded funding for variable-cost cloud operations; optional Premium  
**Visual baseline:** Light PETi visual language represented by the supplied reference screens

---

# 1. Purpose of this specification

This document converts the supplied PETi visual concepts into an implementable Android UI/UX contract.

It defines:

- visual language;
- information architecture;
- navigation;
- every visible screen represented in the concepts;
- additional required screens/states implied by those flows;
- user actions;
- system actions;
- asynchronous events;
- error states;
- permission states;
- cloud-cost funding states;
- rewarded-ad interactions;
- AI result semantics;
- provenance;
- safety presentation;
- empty/loading/offline states;
- accessibility;
- analytics events;
- stable testing identifiers;
- cross-screen interaction rules.

The mockups establish the **visual direction and product personality**.

They are not automatically authoritative for medical wording, monetization, product scope or cloud architecture.

Where a mockup conflicts with the current PETi functional/technical/architecture specification, this document corrects the mockup behavior.

---

# 2. Canonical interpretation of the supplied mockups

The supplied mockups are accepted as the primary visual inspiration for PETi.

The following aspects should be preserved:

- warm off-white background;
- teal PETi brand;
- restrained orange accent;
- large friendly pet photography;
- generous rounded cards;
- soft shadows;
- visually light interfaces;
- strong hierarchy;
- friendly line icons;
- large clear CTAs;
- concise card-based summaries;
- prominent provenance labels;
- calm safety messaging;
- playful but professional decorative hearts/paws;
- low visual density;
- clear separation between data groups.

Several mockup concepts, however, require correction.

---

# 3. Required corrections to the reference mockups

## 3.1 PETi is no longer dog-only

Mockup copy such as:

> “Todo lo que tu perro necesita”

becomes product-level copy such as:

> “Everything your pet needs, in one caring place.”

or:

> “Care better for your pet.”

Dog-specific copy remains appropriate inside a selected `DOG` profile or Dog-only AI capability.

The UI must never use dog terminology for a cat, rabbit, bird or other supported profile.

---

# 3.2 Google sign-in only

One mockup contains:

- Continue with Google;
- Continue with email.

The current product contract supports Google identity.

Therefore:

**Keep:**

`Continue with Google`

**Remove:**

`Continue with email`

unless authentication requirements are explicitly changed in a future specification.

---

# 3.3 No mandatory plan before useful product access

Some mockups show:

- monthly analysis plan;
- “Plan Amigo”;
- analysis limits;
- “Upgrade plan”.

This is not the default PETi Free model anymore.

PETi is useful without payment.

The new system uses:

- included free Cloud Credits/allowance;
- existing rewarded credits;
- sponsor/promotional credits where applicable;
- optional Premium;
- explicit rewarded-ad funding when necessary.

The user is not pushed into a paywall during normal browsing.

---

# 3.4 No ambient advertising

No reference screen should contain:

- banner ads;
- feed ads;
- automatic interstitials;
- sponsored cards among normal Home content.

Advertising appears only inside an explicit **funding flow** for a cloud-cost operation.

---

# 3.5 Health scores are not supported by the current product contract

Mockup examples show:

- `Health score 84/100`;
- `General health 92/100`;
- `Excellent`;
- health gauges.

These must **not ship** unless PETi later defines and independently validates a deterministic Health Score product.

For the current product, replace them with factual summaries such as:

> No current safety alerts

> 3 care items due this week

> Latest measured weight: 28.6 kg

> 2 new observations this week

> Not enough comparable history for a trend

No synthetic universal health score is displayed.

---

# 3.6 No fabricated activity data

Mockup examples show:

- distance walked;
- calories;
- active minutes;
- sleep hours;
- hydration quality.

PETi currently has no wearable/location/activity-tracking contract producing those values.

Therefore these values may appear only when backed by a legitimate future data source.

The UI must never fabricate them from ordinary app usage or media.

---

# 3.7 “Possible causes” must become “possible interpretations”

A symptom mockup lists items such as:

- infection;
- virus;
- dietary cause.

This framing is too diagnostic.

Canonical heading:

**Possible interpretations**

or:

**Things that could be compatible with what you reported**

Every item remains conditional and non-diagnostic.

---

# 3.8 No unsourced treatment instructions

The symptom mockup includes an instruction similar to:

> avoid food for 12 hours...

This must not be generated as generic PETi medical treatment advice.

PETi may instead say:

> Keep a note of vomiting frequency and whether your pet can keep water down.

> Follow any existing instructions from your veterinarian.

> Contact a veterinarian if the listed warning signs occur.

Specific dietary/medication treatment instructions require a legitimate source and product policy.

---

# 3.9 “Normal blood analysis” must not be overstated

A timeline mockup says:

> Everything within normal ranges.

and:

> The complete blood analysis shows no abnormalities. Excellent!

PETi must preserve source-laboratory semantics.

Preferred:

> No source-lab abnormal flags were identified in the reviewed values.

or:

> The displayed results were not marked abnormal by the source laboratory.

This does not imply absence of disease.

---

# 3.10 Document-derived information is not “Observed by PETi”

One mockup labels document-derived blood results:

> Observed by PETi

This is incorrect provenance.

Correct options:

**From document — review needed**

before confirmation.

**Confirmed record**

after review.

**Documented**

for a value explicitly contained in a source record.

---

# 3.11 Medication dose information may be stored, not generated

The mockups show examples such as:

> Apoquel 16 mg

PETi may display such information when:

- entered by the owner;
- imported from a confirmed veterinary record;
- already part of a veterinarian-defined schedule.

PETi must not invent or calculate medication dosing.

---

# 3.12 Body Check wording must remain observational

Mockup:

> detect changes in time and prevent health problems.

Canonical:

> Track visible changes over time and keep useful observations organized.

PETi does not claim that Body Check prevents disease.

---

# 3.13 Stool analysis wording

Mockup:

> evaluates stool quality and digestive health.

Canonical:

> Describes visible stool appearance and helps you track changes over time.

It does not diagnose digestive health from a photograph.

---

# 3.14 Photo analysis wording

Mockup:

> Detect physical details...

Canonical:

> Observe supported visible features such as posture, coat or body appearance.

---

# 4. Experience personality

PETi should feel like:

**a very good pet-care companion**

rather than:

- hospital software;
- a toy;
- a social app;
- a diagnostic device;
- an advertising app;
- an AI chatbot with no structure.

Desired emotional qualities:

- warm;
- calm;
- optimistic;
- competent;
- trustworthy;
- transparent;
- concise;
- non-judgmental;
- reassuring without false reassurance.

---

# 5. Visual design system

## 5.1 Primary palette

### Canvas

Warm ivory:

`#FFFDF7`

Used as the dominant background.

Avoid pure clinical white as the full-page canvas.

### Surface

`#FFFFFF`

Used for:

- cards;
- dialogs;
- forms;
- bottom sheets.

### PETi Primary Teal

Approximate visual target:

`#13A996` to `#35B7A5`

Used for:

- primary CTA;
- selected navigation;
- important icons;
- positive neutral brand emphasis.

### Dark Teal

Approximate:

`#0C4A4A` / `#176E64`

Used for:

- major headings;
- accessible teal text;
- navigation labels.

### Orange Accent

Approximate:

`#FF851B`

Used for:

- small decorative hearts;
- attention details;
- certain secondary states;
- accents and illustrative features.

It should not compete with teal for primary CTA ownership.

### Coral

Used for:

- safety-adjacent attention;
- due/overdue;
- caution surfaces.

### Soft Mint

Used for:

- positive informational backgrounds;
- confirmed states;
- low-attention provenance cards.

### Soft Blue

Used for:

- measurements;
- information;
- neutral educational elements.

### Soft Purple

May identify:

- document/reference information;
- specialized content categories.

---

# 5.2 Semantic colors

Color alone is never sufficient.

Every semantic state uses:

- text;
- icon;
- color.

States:

**Success**

Green/teal + check + text.

**Informational**

Blue/teal + information icon + text.

**Caution**

Amber/orange + warning icon + text.

**Urgent**

Coral/red + shield/warning icon + explicit action.

**Pending**

Yellow/orange + clock/progress + text.

**Unavailable**

Neutral gray + explanatory text.

---

# 5.3 Typography

Recommended hierarchy:

| Role | Size |
|---|---:|
| Hero | 30–36 sp |
| Screen title | 24–28 sp |
| Large section | 20–22 sp |
| Card title | 16–18 sp |
| Body | 15–16 sp |
| Supporting | 13–14 sp |
| Metadata | 12–13 sp |

Primary headings:

- bold;
- dark teal;
- short;
- sentence case.

Avoid large blocks of centered body copy.

---

# 5.4 Shape

Cards:

`16–20 dp` radius.

Hero/photo cards:

up to `24 dp`.

Buttons:

`14–18 dp` radius.

Use rounded geometry consistently.

Avoid mixing sharp rectangular controls into the PETi visual language.

---

# 5.5 Spacing

Base grid:

`8 dp`.

Primary screen edge:

`16–20 dp`.

Common vertical groups:

- 8;
- 12;
- 16;
- 24;
- 32 dp.

---

# 5.6 Shadows

Use subtle elevation.

Cards should feel physically separated without looking floating/heavy.

Avoid exaggerated Material shadows.

---

# 5.7 Photography

Real pet photography should dominate:

- profile;
- onboarding;
- capture;
- selected-pet cards.

Photography must not imply unsupported health findings.

Generic species imagery is decorative only.

---

# 5.8 Decorative elements

Small:

- hearts;
- paws;
- curved background shapes;
- sparkle marks.

Use sparingly.

They must never interfere with:

- safety content;
- clinical records;
- destructive controls.

---

# 6. Canonical source/provenance visual system

This is one of PETi's most important UX systems.

## 6.1 Observed by PETi

Icon:

eye / PETi shield / observation icon.

Color:

teal.

Text:

**Observed by PETi**

Meaning:

A supported visible/audible feature extracted from media.

---

# 6.2 Reported by you

Icon:

person/chat.

Color:

orange or neutral blue.

Text:

**Reported by you**

Meaning:

Owner-provided context.

---

# 6.3 From document — review needed

Icon:

document + clock/caution.

Text:

**From document — review needed**

Meaning:

AI extraction proposal.

Not canonical yet.

---

# 6.4 Confirmed record

Icon:

document + check/shield.

Text:

**Confirmed record**

Meaning:

Owner-reviewed record fact.

---

# 6.5 Documented

Text:

**Documented**

Meaning:

Explicit value in source document.

---

# 6.6 Measured

Icon:

scale / thermometer / ruler.

Text:

**Measured**

---

# 6.7 Estimated

Icon:

sparkle/range.

Text:

**Estimated**

Never style Estimated like Measured.

---

# 6.8 Possible interpretation

Icon:

brain/lightbulb.

Text:

**Possible interpretation**

Never just:

> Diagnosis

or:

> Cause

---

# 6.9 Safety guidance

Icon:

shield.

Text depends on state:

- Monitor;
- Professional review recommended;
- Contact a veterinarian;
- Urgent veterinary contact.

---

# 7. Canonical application navigation

The reference boards show several conflicting bottom-navigation arrangements.

The canonical PETi navigation should be unified.

## Primary navigation

Five destinations:

1. **Home**
2. **Analyze**
3. **Timeline**
4. **Care**
5. **Pet**

### Home

Daily useful overview.

### Analyze

AI and media operations.

### Timeline

Canonical chronological history.

### Care

Reminders/calendar/Body Check.

### Pet

Profile, Measurements, Records, Documents, Settings.

---

# 7.1 Analyze destination

Analyze may receive stronger visual prominence than the other tabs.

It must remain a standard accessible navigation item.

---

# 7.2 Documents

Documents are not a permanent top-level bottom-nav destination.

Reachable from:

`Pet → Records & Documents`

and contextual shortcuts.

---

# 7.3 Settings

Settings:

`Pet → Settings`

or account/settings icon.

---

# 7.4 Selected-pet context

All dog/pet-specific top-level surfaces expose the current selected pet.

Pet switcher contains:

- avatar;
- name;
- species;
- optional status.

Tapping opens the Pet Switcher.

---

# 8. SCREEN INVENTORY

# UI-001 — Welcome

Derived from the “Bienvenida y acceso” reference.

## Purpose

Introduce PETi before authentication.

## Layout

Large upper pet photograph.

PETi decorative heart/paw treatment.

Lower curved white/ivory content surface.

Headline:

> **Care better for your pet**

Body:

> Keep observations, care and important records together—with AI assistance when it can genuinely help.

Primary CTA:

**Get started**

Secondary links:

- Privacy;
- Terms;
- Learn about PETi.

## Actions

### Get started

Event:

`welcome_get_started_tapped`

Navigation:

`UI-002 Sign In`

### System Back

Exit app if first destination.

---

# 8.1 Pagination correction

The visual reference contains multiple onboarding dots but does not define the content of the additional pages.

Canonical implementation:

**do not implement an unexplained carousel.**

Either:

- use a single Welcome screen;

or create additional onboarding pages only after explicit product content is defined.

For v1:

single page preferred.

---

# UI-002 — Sign In

## Header

PETi logo.

Tagline:

> **Your companion. Your care.**

## Authentication

Primary:

**Continue with Google**

Google Credential Manager is opened.

No PETi password.

No generic email/password form.

## Legal copy

> By continuing, you agree to PETi's Terms of Use and acknowledge the Privacy Policy and AI/veterinary limitations.

Clickable:

- Terms;
- Privacy;
- AI limitations.

## States

### Idle

Google CTA enabled.

### Credential UI open

PETi waits.

### Server validating

Progress:

> Signing you in…

### Auth error

> We couldn't complete sign-in. Please try again.

CTA:

**Try again**

### Network unavailable

> PETi needs an internet connection to sign you in.

---

# UI-003 — Required Disclosure

Shown when required disclosure versions are not yet accepted.

Sections:

### AI assistance

> PETi uses AI and can be uncertain.

### Veterinary limitation

> PETi helps describe observations and organize information. It does not provide a veterinary diagnosis or replace professional examination.

### Private cloud processing

> Media submitted for AI analysis is processed securely in PETi's cloud services.

Actions:

**Accept and continue**

Links:

- Terms;
- Privacy;
- data details.

---

# UI-010 — My Pets

Derived from “Mis perros”.

Canonical title:

> **My pets**

Not:

> My dogs

unless the account contains only Dog and the product intentionally chooses contextual copy.

## Pet cards

Each card:

- avatar;
- name;
- species/type;
- age/life stage when known;
- profile completeness indicator where useful;
- overflow menu.

Possible states:

**Profile complete**

**Complete profile**

**AI available**

**AI not available yet for this species**

## Overflow

- View profile;
- Edit;
- Change avatar;
- Delete pet.

Delete requires confirmation.

## Add card

CTA:

**Add pet**

Subtitle:

> Add another member of your family.

Action:

`pet_add_tapped`

→ `UI-011`.

---

# UI-011 — Add Pet

Derived from “Agregar perro”.

## Required field

### Name

Label:

**Name**

## Required species

### Species

Search/select:

- Dog;
- Cat;
- Rabbit;
- Bird;
- Horse;
- other supported registry entries.

The exact list is server-driven.

## Optional profile fields

### Breed / type

Species-aware.

### Date of birth

or:

### Approximate age/life stage

### Sex

with Unknown.

### Neutered/spayed status

Only for species where meaningful.

Options:

- Yes;
- No;
- Unknown.

### Measured weight

Optional.

Unit localized.

Do not call it “approximate weight” when user is entering a measurement.

## Primary CTA

**Continue**

## Validation

Blank name:

> Enter your pet's name.

Missing species:

> Choose your pet's species.

No other field blocks creation.

---

# UI-012 — AI Initial Scan Offer

Derived from “Escaneo inicial”.

Displayed only if an enabled SpeciesCapabilityPack supports Initial Scan.

For initial launch this means primarily `DOG`.

## Headline

> **Optional Initial Scan**

Body:

> PETi can use a short video or supported photos to suggest visible profile information.

## Explicit limitation

> These are suggestions, not facts. You can review or change everything.

## May suggest

Dog pack example:

- appearance/type;
- broad life stage;
- size class;
- coat;
- visual body-condition information when enabled.

## Must not suggest as authoritative

- exact age;
- genetic ancestry;
- neuter status;
- precise uncalibrated weight.

## CTA

**Start Initial Scan**

Secondary:

**Skip for now**

Manual profile creation always remains available.

---

# UI-013 — Cloud Funding Gate

This screen/sheet replaces the old mandatory plan model whenever an Initial Scan or other AI operation is not currently funded.

## State A — Included

Do not show funding UI.

Proceed immediately.

## State B — Existing credits

Example:

> Initial Scan · 1 Cloud Credit

> You have 3 credits.

CTA:

**Use 1 credit**

## State C — No credit

Headline:

> **Continue for free**

Copy:

> This AI analysis uses cloud processing. You can watch a short ad to receive PETi Cloud Credits.

CTA:

**Watch ad & get credits**

Secondary:

**Not now**

Optional Premium:

**See PETi Premium**

No ambient ad is displayed.

---

# UI-014 — Rewarded Ad Preparation

Immediately before handing off to the ad SDK.

Display:

> **You'll receive 3 PETi Cloud Credits after the ad is completed.**

CTA:

**Continue**

Secondary:

**Cancel**

The user must explicitly choose Continue.

---

# UI-015 — Reward Verification

States:

### Verifying

> Confirming your credits…

### Success

> **3 Cloud Credits added**

CTA:

**Continue**

### Canceled/not earned

> No credits were used or added.

### Verification failure

> We couldn't verify the reward yet.

CTA:

**Try again**

Never grant local credits optimistically.

---

# UI-020 — Home

Derived from “Inicio y resumen diario” and parts of “Concepto 3”.

## Top area

Greeting:

> Good morning, Ana

Optional:

> Here's what matters for Toby today.

Notification/activity icon.

Selected pet card.

---

# 8.2 Selected Pet Hero Card

Contains:

- photograph;
- name;
- species/type;
- age/life stage;
- pet-switcher affordance.

Do not display arbitrary universal health scores.

Instead show one useful status summary.

Examples:

> No urgent PETi guidance

> 1 reminder due today

> Not enough comparable data for a trend

> Latest Body Check: 6 days ago

---

# 8.3 Next Care

Example:

**Next reminder**

`Vaccination · 20 May`

or:

`Medication · 18:00`

Only display real stored events.

---

# 8.4 Today summary

Only categories with real data appear.

Possible cards:

- Care completed;
- latest measurement;
- recent observation;
- Body Check status;
- recent document review;
- latest AI result.

Do not fabricate:

- distance;
- calories;
- sleep;
- hydration.

---

# 8.5 Next Best Action

Soft highlighted card.

Examples:

> **Review the new analysis result**

> **Body Check is due**

> **2 document facts need review**

> **Add a measured weight**

One obvious action.

---

# 8.6 Home empty state

For a new account:

> **Start building [name]'s history**

Supporting text:

> Add a measurement, create a reminder or make your first observation.

Actions:

**Add measurement**

**Analyze**

---

# UI-021 — Today's Summary

Derived from right-hand “Resumen de hoy” screen.

## Header

Pet avatar.

Name.

Species/type/life stage.

No arbitrary health score.

## Cards

Potential real-data cards:

### Care activity

Example:

> 2 of 3 planned care items completed

### Latest weight

`28.6 kg`

Source:

Measured.

Trend only if enough comparable measurements exist.

### Latest PETi analysis

Summary.

### Upcoming vaccination

Date and source.

### Body Check

Due/completed.

## Data insufficiency

Example:

> Not enough comparable measurements yet.

Do not replace missing data with optimistic status labels.

---

# UI-030 — Analyze Hub

Derived from “Analizar y elegir cómo observar”.

## Header

Pet switcher.

Optional credit summary:

> 3 Cloud Credits

This is useful because Analyze contains cost-bearing operations.

Do not display credits throughout unrelated screens.

## Headline

> **What would you like to observe?**

## Capability cards

Visibility depends on SpeciesCapabilityPack.

Dog launch pack may eventually show:

### Video

> Observe behavior and movement in context.

### Audio

> Record sounds and vocalization patterns.

### Photo

> Describe supported visible features.

### Stool / Feces

> Describe visible stool appearance and track changes.

### Dental

> Guided photos of visible teeth and gums.

### Body Check

> Guided periodic visual body observations.

### Veterinary document

> Add a private veterinary document.

Document upload itself may use storage but is not an AI pet observation.

## Disabled capability

Example:

> Dental Check isn't available for cats yet.

Do not send it to Dog analysis.

---

# UI-031 — Audio Guide

Derived from “Guía para Audio”.

## Header

**Audio guide**

## Intro

> Record a clear sample so PETi can describe supported acoustic patterns in context.

## Capture tips

- choose a reasonably quiet environment;
- keep the phone at a safe distance;
- avoid deliberately provoking vocalization;
- avoid TV/music where possible;
- recommended duration shown by current capability contract.

## PETi can

> Describe audible patterns and use the context you provide.

## PETi cannot

> Literally translate what your pet is “saying”.

> Diagnose disease from sound alone.

Primary:

**Continue**

---

# UI-032 — Cloud Credits & AI Usage

Replaces the old “Mi plan y análisis” as the default resource page.

## Header

> **Cloud Credits**

## Available credits

Large balance.

Example:

`3 credits available`

## Included/free allowance

If applicable:

> Next free allowance refresh: Monday

## Recent use

Examples:

- Video Check · 2 credits;
- Dental Check · 2 credits;
- Photo Check · 1 credit.

## Funding

CTA:

**Get credits by watching an ad**

Optional:

**PETi Premium**

## Economic transparency

Short help:

> Cloud Credits help fund AI processing and additional cloud resources. Ordinary PETi browsing does not use credits.

---

# UI-040 — Video Capture Guide

Derived from “Capturar video”.

## Header

Back.

Title:

**Capture video**

Info icon.

## Main guidance

Dog example:

> **Record a clear video of Rocky**

> Keep the relevant part of the body visible and capture natural behavior safely.

Do not require a specific pose unless the analysis protocol does.

## Video preview/live camera

Rounded capture area.

Safe framing overlays.

Timer.

Example:

`00:20`

## Tips

Depending on analysis:

- include natural movement where relevant;
- use adequate light;
- avoid heavy backlighting;
- keep one target pet clearly visible.

## Safety rule

Never instruct:

- provoke fear;
- make the pet limp;
- force movement;
- create aggression;
- force mouth opening.

## Controls

### Gallery

System picker.

### Record

Large central button.

### Back

Cancel.

---

# UI-041 — Media Preview

Required even though not explicitly shown as its own reference screen.

Contains:

- video/photo/audio preview;
- duration;
- selected pet;
- selected analysis type.

Actions:

**Use this**

**Retake**

**Choose another**

For video where supported:

**Trim**

---

# UI-042 — Context & Question

Before interpretive analysis.

## Question

> **What are you trying to understand?**

Required for interpretation flows.

Free text.

## Immediate context

> **What happened just before this?**

Badge:

**Reported by you**

Can be:

`I don't know`

## Additional structured context

Analysis-specific.

Must never silently treat answers as observed facts.

---

# UI-043 — Analysis Funding Confirmation

Before accepted submission.

If already funded:

show simple confirmation only when useful.

Example:

> Video analysis · 2 Cloud Credits

> Available: 5 credits

CTA:

**Analyze**

After accepted click:

- reserve credits server-side;
- disable duplicate submit;
- continue.

If not funded:

open `UI-013`.

---

# UI-044 — Upload & Analysis Progress

Required cloud-only state.

## State sequence

### Preparing

> Preparing your recording…

### Uploading

> Uploading securely…

Show determinate percentage when known.

### Queued

> Your analysis is queued.

### Processing

> PETi is analyzing the evidence.

### Validating

> Checking the result…

### Completed

Automatically navigate or notify.

## Important message

> You can leave this screen. PETi will continue processing.

Actions:

**Go to Home**

where safe.

---

# UI-045 — Needs Retake

Examples:

> **We need a clearer recording**

Reason:

> Rocky was too small in the frame.

or:

> The recording was too dark.

or:

> More than one pet was visible.

Action:

**Try again**

Secondary:

**Cancel**

When technical preflight has not consumed the operation:

> This attempt did not use your Cloud Credit.

---

# UI-046 — Insufficient Evidence

Different from technical failure.

Headline:

> **Not enough reliable evidence**

Copy:

> The recording was processed, but PETi cannot support a specific interpretation from it.

Give concrete improvement advice.

Do not fabricate an answer.

---

# UI-047 — Analysis Result

Derived from “Resultado del análisis”.

## Header

Title:

**Analysis result**

Status:

**Analysis complete**

Do not use celebratory language when the result contains concerning guidance.

For normal results, mild positive visual language is acceptable.

## Pet summary

- pet image;
- name;
- species/type;
- date/time;
- analysis type.

---

# 8.7 Provenance section

### Observed by PETi

Examples:

> Relaxed standing posture in the visible segment.

> Head orientation changed repeatedly between 00:06–00:10.

No interpretation here.

### Reported by you

Example:

> No recent diet change.

### Possible interpretation

Example:

> One possible explanation, given the observed posture and your context, is...

Always conditional.

---

# 8.8 Findings summary

Use only real output fields.

Possible cards:

- posture;
- movement;
- coat;
- body appearance;
- sound pattern;
- stool appearance.

Do not show:

> Ideal

unless a validated and properly scoped classification supports it.

---

# 8.9 Safety card

Normal state:

> **Safety guidance**

> No urgent PETi safety rule was triggered by the information available.

Then limitation:

> PETi does not replace a veterinary examination.

Concerning state:

use corresponding deterministic safety wording.

---

# 8.10 Result actions

Primary:

**Save / View in Timeline**

If results auto-save:

label instead:

**View in Timeline**

Secondary:

**View details**

Optional:

**Ask about this result**

if bounded assistant is enabled.

---

# UI-048 — Analysis Details

Shows:

- complete observations;
- timestamps;
- interpretations;
- alternatives;
- confidence;
- limitations;
- source media availability;
- safety;
- evidence;
- provenance.

Expandable:

**About this analysis**

Contains:

- analysis ID;
- model;
- prompt version;
- schema version;
- safety version;
- Species Capability Pack;
- timestamp.

No chain-of-thought.

---

# UI-050 — PETi Guided Assistant

Derived from “Asistente PETi”.

This should be a **bounded guided care/observation assistant**, not unrestricted veterinary diagnosis.

## Header

> **PETi Assistant**

Selected pet shown.

## Conversation

Owner message:

> My dog vomited twice today and doesn't want to eat. What should I do?

PETi first response should:

- acknowledge;
- state limitation;
- gather necessary context;
- avoid premature diagnosis.

Example:

> Thanks for the context. I can help organize what you're observing and check for warning signs. I can't determine the cause or diagnose your pet.

---

# 8.11 Guided questions

Example:

> **When did this begin?**

Choices:

- Today;
- Yesterday;
- 2–3 days ago;
- More than 3 days;
- Not sure.

---

# 8.12 Symptom/report chips

Heading:

> **Which of these have you noticed?**

Examples:

- vomiting;
- diarrhea;
- loss of appetite;
- lethargy;
- apparent abdominal discomfort;
- measured temperature concern.

Do not use **Fever** unless it is clearly owner-reported or based on a measured temperature.

Multiple selection.

Badge semantics:

everything here is:

**Reported by you**

---

# 8.13 Free text

Input:

> Add more context…

Send button.

The assistant must not silently alter canonical health records.

If the owner wants to save durable information:

explicit:

**Add to Timeline**

---

# UI-051 — Symptom Summary

Derived from “Resumen de síntomas”.

## Section: Safety/Urgency

Use the canonical deterministic safety state, not invented severity labels such as “mild to moderate” unless part of the approved safety taxonomy.

Examples:

**Monitor**

**Professional review recommended**

**Contact a veterinarian**

**Urgent veterinary contact**

Under it:

> This is guidance based on the information you supplied, not a diagnosis.

---

# 8.14 Possible interpretations

Heading:

**Possible interpretations**

Never:

**Possible causes**

if that implies diagnosed etiology.

Example:

> Several different situations can produce these signs. PETi cannot determine which one applies without veterinary assessment.

Potential categories may be presented only when supported and safely worded.

---

# 8.15 What to do now

Safe actions may include:

- keep track of frequency;
- record whether water is being retained;
- note new symptoms;
- keep source veterinary instructions available;
- consider contacting a veterinarian depending on safety state.

Do not give medication dosage.

Do not prescribe food withholding unless a valid product rule explicitly allows it.

---

# 8.16 Warning signs

Prominent card:

> **When to contact a veterinarian**

List comes from deterministic safety rules.

Example categories may include reported:

- repeated vomiting;
- blood;
- marked lethargy;
- collapse;
- inability to keep water down;
- severe pain.

Do not invent symptoms the owner did not report.

---

# 8.17 Actions

### Monitor symptoms

Creates a structured tracking flow.

### Prepare for veterinary contact

May:

- summarize observations;
- prepare record;
- show veterinarian contact already stored in profile.

The current PETi core does not require location search.

Therefore do not promise:

> Find a veterinarian near you

unless a future location/business-search feature is explicitly added.

---

# UI-060 — Timeline

Derived from “Línea de tiempo e historial”.

## Header

Pet avatar.

Example:

> **Rocky's Timeline**

Species/type/life stage.

## Filters

Canonical:

- All;
- Observations;
- Records;
- Measurements;
- Care;
- Body Checks;
- Reports.

Additional filter button:

- date range;
- source;
- analysis type.

---

# 8.18 Timeline entry

Every entry shows:

- time/date;
- event icon;
- title;
- one-line summary;
- provenance badge;
- chevron.

Examples:

### AI result

`Observed by PETi`

### Owner note

`Reported by you`

### Weight

`Measured`

### Document

`From document — review needed`

### Clinical fact

`Confirmed record`

### Reminder

`Care`

---

# 8.19 Add record

Button:

**Add**

Opens a sheet:

- Measurement;
- Owner note;
- Reminder;
- Document;
- Analysis.

---

# 8.20 Empty Timeline

> **Nothing recorded yet**

> Your pet's Timeline will bring observations, measurements, care and records together.

CTA:

**Add first record**

---

# UI-061 — Timeline Record Detail

Derived from “Detalle del registro”.

## Header

Type-specific title.

Example:

**Documented lab result**

Date/time.

## Status

Avoid unsupported claims.

Example:

> No source-lab abnormal flags were recorded in the reviewed values.

---

# 8.21 Source & provenance

Example:

**Confirmed record**

> Reviewed from `Results_Laboratory.pdf`.

or:

**From document — review needed**

before review.

---

# 8.22 Evidence

Source document card:

- thumbnail;
- name;
- size/type;
- page if relevant.

Action:

**View source**

---

# 8.23 Metadata

- date;
- time;
- provider/clinic if source;
- reference ID;
- owner note.

---

# 8.24 Actions

**Add context**

**Share**

**View evidence**

Share must not create a public permanent URL.

---

# UI-070 — Today's Care

Derived from “Recordatorios de hoy”.

## Header

> **Today's care**

Date.

## Reminder cards

Examples:

### Medication

Source/schedule displayed.

If dose exists:

> Apoquel 16 mg

must come from an owner/veterinary source.

### Walk

Owner-created routine.

### Grooming

Owner-created routine.

### Veterinary appointment

Calendar item.

---

# 8.25 Reminder states

**Upcoming**

**Due**

**Overdue**

**Completed**

**Snoozed**

Use text + icon, not color only.

---

# 8.26 Reminder actions

Tap card → Reminder Detail.

Quick complete where appropriate.

Never use one-tap completion if accidental completion could be problematic without undo.

---

# UI-071 — Care Calendar

Derived from “Calendario de cuidados”.

## Header

**Care calendar**

Month navigation.

## Calendar

Selected date.

Events indicated accessibly.

## Upcoming events

List underneath.

Examples:

- vaccination;
- medication;
- walk;
- grooming;
- vet appointment.

## Add

CTA:

**Add event**

---

# UI-073 — Create/Edit Reminder

Fields:

- pet;
- type;
- title;
- date;
- time;
- timezone;
- recurrence;
- optional note;
- source.

Source choices:

- Entered by you;
- Veterinarian plan entered by you;
- Confirmed document;
- PETi suggestion where product permits.

No dose generation.

---

# UI-072 — Body Check Overview

Derived from Body Check reference.

## Header

**Body Check**

Help icon.

## Status banner

Examples:

**Body Check due**

or:

**Last Body Check: 10 May**

## Explanation

Canonical:

> A guided periodic review to keep visible changes and useful observations organized over time.

Do not claim:

> prevents health problems.

---

# 8.27 Body Check overview illustration

The reference dog with labeled regions is useful.

For dog pack:

- ears;
- eyes;
- coat/skin;
- paws;
- stool;
- weight.

Important distinction:

These may route to different data types.

Example:

**Stool** → Feces Check.

**Weight** → measured entry.

**Dental** could be another specialist flow.

Body Check itself must not merge all of them into one unsupported diagnostic score.

---

# 8.28 Progress

Example:

`0 of 6 observations completed`

This is checklist progress, not a health score.

CTA:

**Start Body Check**

---

# UI-080 — Pet Profile

Derived from “Perfil de Rocky”.

## Header

Pet name.

Edit icon.

Hero pet photo.

Avatar/photo action.

## Facts

- name;
- species;
- owner-confirmed breed/type;
- sex;
- reproductive status;
- DOB;
- approximate life stage;
- latest measured weight;
- microchip where entered;
- veterinarian contact where entered.

Every fact should expose provenance where material.

---

# 8.29 Profile completeness

May say:

**Profile complete**

only to indicate profile-field completion.

Never imply:

**Pet healthy**

---

# 8.30 Quick links

- Care;
- Timeline;
- Measurements;
- Records & Documents;
- Body Check;
- Settings.

---

# UI-081 — Measurements

Derived from “Mediciones”.

## Sections

### Weight history

Graph if enough records.

Chart must have textual summary.

### Add measurement

Value.

Unit.

Date/time.

Method/source.

CTA:

**Save measurement**

---

# 8.31 Body-condition section

Display only when an enabled certified Body Check capability exists.

Example:

**Visual body-condition range**

Badge:

Estimated.

Never label as measured.

---

# 8.32 Temperature

Persistent educational card:

> **PETi does not measure core body temperature with your phone.**

CTA:

**Add measured temperature**

Temperature form asks:

- value;
- °C/°F;
- measurement method;
- timestamp;
- note.

---

# UI-082 — Clinical Records

Derived from “Registros clínicos”.

## Sections

Possible:

- Vaccinations;
- Medications;
- Allergies;
- Conditions;
- Procedures;
- Provenance;
- Other.

## Every row shows source

Examples:

**Confirmed record**

**Documented**

**Reported by you**

Never visually merge them.

---

# 8.33 Add Record

CTA:

**Add record**

Possible paths:

- Manual;
- From document.

---

# UI-090 — Documents

Derived from “Documentos”.

## Header

**Documents**

Upload icon.

## Filter chips

Possible:

- All;
- Veterinary;
- Vaccinations;
- Labs;
- Other.

## Document cards

Show:

- title;
- pet;
- date;
- type;
- size;
- status.

Statuses:

**Uploaded**

**Extracting**

**Review needed**

**Reviewed**

**Extraction failed**

---

# 8.34 Review-needed banner

> **Document facts need review**

> PETi found information that must be reviewed before it becomes part of your pet's confirmed record.

CTA:

**Review now**

---

# UI-091 — Document Review

Derived from “Revisión de documento”.

## Header

**Review document**

Banner:

> **From document — review needed**

Supporting:

> Review and confirm the extracted facts. Confirmed information will be saved with its source.

## Document information

- title;
- pet;
- date;
- status.

## Candidate facts

Each row:

- label;
- proposed value;
- source page/anchor where possible;
- edit button.

Example:

`RBC · 6.8 ×10⁶/µL`

Original source units preserved.

---

# 8.35 Actions per fact

**Confirm**

**Correct**

**Reject**

## Bottom actions

**Edit**

**Confirm selected**

Do not offer a misleading global confirm if unreviewed material facts cannot safely be bulk-confirmed.

---

# UI-092 — Settings

Derived from “Ajustes”.

## Account card

- profile identity;
- pet avatars/names;
- account entry.

## Funding/Premium section

Replace old compulsory plan semantics with:

### PETi Free / PETi Premium

Show:

- current status;
- Cloud Credit allowance;
- retained media allowance where relevant.

CTA:

**Cloud Credits**

Optional:

**PETi Premium**

---

# 8.36 Preferences

- Notifications;
- Reminders;
- Units;
- Language.

---

# 8.37 Privacy & Data

- Privacy center;
- Media retention;
- AI/cloud processing;
- Research consent if offered;
- Export data;
- Delete account.

---

# 8.38 Permissions

- Camera;
- Microphone;
- Notifications.

No location permission unless a future explicit feature needs it.

---

# 8.39 Legal

- Terms;
- Privacy;
- AI/veterinary limitations;
- app version.

---

# UI-100 — Alternative Concept-3 Dashboard

One supplied board is visually labeled **Concept 3**.

It is **not the canonical visual direction** because the rest of the reference set consistently uses the lighter Concept-2 PETi language.

Useful concepts that may be retained:

- clean modular cards;
- selected pet prominently visible;
- next reminder emphasis;
- compact summary architecture.

Do not retain from this concept without separate requirements:

- universal health score;
- calories;
- walking distance;
- activity progress;
- arbitrary daily targets.

Use Concept 3 only as secondary layout inspiration.

---

# 9. CLOUD FUNDING UX

This is a major new UX system not shown in the original boards.

# 9.1 Fundamental rule

No user sees an ad because they:

- opened Home;
- viewed Timeline;
- opened Care;
- edited a pet;
- viewed a result.

An ad may only be offered because they explicitly requested a **materially costly cloud operation** and need funding.

---

# 9.2 Cost-bearing operation examples

Potential:

- Gemini photo analysis;
- Gemini video analysis;
- audio analysis;
- Dental Check;
- Feces Check;
- AI Body Check;
- AI document extraction;
- AI Weekly Report;
- additional retained cloud media.

---

# 9.3 Normal funded flow

User taps:

**Analyze**

Backend says funded.

No funding screen.

Operation begins.

---

# 9.4 Reward-required flow

Bottom sheet:

> **This operation uses cloud processing**

> Video analysis requires 2 Cloud Credits.

> You currently have 0.

Primary:

**Watch an ad & get 3 credits**

Secondary:

**Not now**

Optional tertiary:

**PETi Premium**

No advertiser content appears yet.

---

# 9.5 Storage funding

When included retained storage is exhausted:

> **Keep this original video?**

Option A:

**Analyze and use standard retention**

No additional storage credit if policy allows.

Option B:

**Keep original longer · 1 Cloud Credit**

If no credit:

rewarded funding may be offered.

Do not show an ad for every upload.

---

# 9.6 Ad unavailable

> **No rewarded ad is available right now**

Options:

- Try again later;
- use existing credits if available;
- PETi Premium;
- cancel.

Do not block access to existing information.

---

# 10. ASYNCHRONOUS SYSTEM STATES

Canonical AI job states:

## DRAFT

Not submitted.

## PREPARING

> Preparing your media…

## UPLOADING

> Uploading securely…

## QUEUED

> Queued for analysis.

## PROCESSING

> PETi is analyzing the evidence.

## VALIDATING

> Checking the result.

## COMPLETED

> Analysis ready.

## NEEDS_RETAKE

> We need a clearer capture.

## INSUFFICIENT_EVIDENCE

> There isn't enough reliable evidence for a specific interpretation.

## FAILED_RETRYABLE

> Something interrupted processing. You can retry safely.

## FAILED_FINAL

> We couldn't complete this analysis.

Show support/correlation ID.

---

# 11. OFFLINE UX

Because PETi AI is cloud-only:

## Cached content

May remain readable:

- pet profiles;
- recent Timeline;
- Care;
- previously cached result summaries.

Banner:

> **Offline — some information may be out of date**

## AI action

Disabled or intercepted:

> **Internet connection required**

> PETi's AI analysis runs securely in the cloud.

## Upload interrupted

> Upload paused. We'll continue when your connection returns.

Only if WorkManager-safe resume is implemented.

---

# 12. PERMISSION UX

# 12.1 Camera

Requested only when user chooses:

- camera capture;
- Initial Scan;
- Body Check capture.

Pre-permission explanation:

> PETi needs camera access only when you choose to capture media.

Denied:

**Choose existing media**

where applicable.

Permanent denied:

**Open Settings**

---

# 12.2 Microphone

Requested only for audio-enabled flows.

Never as a startup permission.

---

# 12.3 Photo/video library

Use Android Photo Picker.

Do not request broad gallery access.

---

# 12.4 Documents

Use SAF/document picker.

No all-files permission.

---

# 12.5 Notifications

If denied:

> Your reminders are still saved, but device notifications are off.

Action:

**Open notification settings**

---

# 13. SAFETY UI SYSTEM

Safety must be visually consistent across every feature.

## NORMAL INFORMATION

White/teal.

No alarming banner.

## MONITOR

Soft blue/amber.

Heading:

**Monitor**

## PROFESSIONAL REVIEW RECOMMENDED

Amber.

Heading:

**Professional review recommended**

## CONTACT VETERINARIAN

Strong amber/coral.

Heading:

**Contact a veterinarian**

## URGENT VETERINARY CONTACT

Red/coral high-emphasis card.

Heading:

**Seek urgent veterinary care**

Only deterministic policy can create this state.

## SAFETY BLOCKED

> PETi can't provide that kind of guidance.

Safe redirection.

---

# 14. SAFETY DISPLAY RULES

Never put:

- ads;
- upsells;
- sponsorship;
- Premium CTA

inside an urgent safety card.

Never hide safety content behind:

- accordion that defaults closed;
- paywall;
- ad;
- extra credit;
- “View more”.

Safety guidance is immediately visible once the operation has completed.

---

# 15. STANDARD EMPTY STATES

## No pets

> **Add your first pet**

## No Timeline

> **Nothing recorded yet**

## No measurements

> **No measurements yet**

CTA:

**Add measurement**

## No reminders

> **Nothing scheduled**

CTA:

**Create reminder**

## No documents

> **Your private document vault is empty**

CTA:

**Add document**

## No analysis history

> **No PETi analyses yet**

CTA:

**Analyze**

## Insufficient trend

> **Not enough comparable history yet**

Never render fake trend graphics.

---

# 16. LOADING STATES

Use skeleton content for:

- Home;
- Timeline;
- Care;
- Pet profile;
- Documents.

Use phase-specific progress for:

- upload;
- extraction;
- AI analysis;
- account deletion.

Never use an indefinite spinner alone for long cloud work.

---

# 17. ERROR SYSTEM

Every error contains:

1. clear title;
2. customer-safe explanation;
3. recovery action;
4. support ID for permanent cloud failure where appropriate.

Examples:

### Network

> **You're offline**

### Authorization

> **You don't have access to this item**

Do not leak its existence across accounts.

### Media

> **This file couldn't be read**

### AI provider retryable

> **Analysis was interrupted**

CTA:

**Retry**

### Permanent

> **We couldn't complete this analysis**

`Support ID: ABC123`

---

# 18. DESTRUCTIVE ACTIONS

Use explicit confirmation for:

- delete pet;
- delete document;
- delete analysis/source media;
- delete account.

Confirmation explains exact impact.

Example:

> **Delete Rocky?**

> This will remove Rocky's profile and associated PETi data according to the deletion policy. This cannot be undone.

Primary destructive:

**Delete Rocky**

Secondary:

**Cancel**

---

# 19. DEEP LINK BEHAVIOR

Supported targets should include:

- analysis result;
- reminder;
- Body Check;
- Weekly Report;
- pet profile;
- document;
- record.

Deep link flow:

`open link → authenticate if necessary → ownership validation → destination`

Unavailable/deleted item:

> This item is no longer available.

Never leak cross-user metadata.

---

# 20. MESSAGE CATALOG

## AI limitation

> PETi helps describe observations and organize information. It does not provide a veterinary diagnosis.

## No baseline

> PETi needs more comparable observations before it can show a personal trend.

## Stability

> No meaningful change was detected in the comparable records from this period.

## Insufficient history

> Not enough comparable information is available to assess change.

## AI profile suggestion

> Suggested by PETi — please review or edit.

## Weight

> Add a measured weight for the most reliable record.

## Temperature

> PETi does not measure core body temperature with your phone.

## Document

> Extracted from your document — review before adding it to your pet's confirmed record.

## Notification disabled

> Your reminders are saved, but device notifications are off.

## Cloud operation

> This operation uses cloud processing.

## Reward

> Watch a short ad to receive PETi Cloud Credits.

## Ad cancellation

> No credits were used or added.

## Unsupported species

> AI analysis for this species isn't available yet.

---

# 21. EVENT / ANALYTICS CONTRACT

Analytics must not contain:

- raw media;
- document text;
- owner free text;
- veterinary results;
- signed URLs;
- tokens.

Use opaque IDs.

---

# 21.1 Authentication events

`welcome_viewed`

`welcome_get_started_tapped`

`google_signin_tapped`

`google_signin_succeeded`

`google_signin_failed`

`legal_disclosure_viewed`

`legal_disclosure_accepted`

---

# 21.2 Pet events

`pet_list_viewed`

`pet_add_started`

`pet_created`

`pet_profile_viewed`

`pet_profile_edit_started`

`pet_profile_saved`

`pet_switched`

`pet_delete_started`

`pet_deleted`

---

# 21.3 Initial Scan

`initial_scan_offered`

`initial_scan_started`

`initial_scan_skipped`

`initial_scan_capture_started`

`initial_scan_capture_completed`

`initial_scan_submitted`

---

# 21.4 Funding events

`cloud_cost_estimate_requested`

`funding_required_shown`

`cloud_credit_balance_viewed`

`rewarded_ad_offer_viewed`

`rewarded_ad_accepted`

`rewarded_ad_canceled`

`rewarded_ad_completed`

`reward_verification_started`

`reward_verification_succeeded`

`reward_verification_failed`

`cloud_credit_granted`

`cloud_credit_reserved`

`cloud_credit_consumed`

`cloud_credit_released`

---

# 21.5 Analysis

`analyze_hub_viewed`

`analysis_type_selected`

`analysis_capture_started`

`analysis_media_selected`

`analysis_context_completed`

`analysis_submit_requested`

`analysis_upload_started`

`analysis_queued`

`analysis_processing`

`analysis_completed`

`analysis_needs_retake`

`analysis_insufficient_evidence`

`analysis_failed_retryable`

`analysis_failed_final`

`analysis_result_viewed`

`analysis_details_viewed`

---

# 21.6 Timeline

`timeline_viewed`

`timeline_filter_changed`

`timeline_entry_viewed`

`timeline_context_added`

`timeline_source_opened`

---

# 21.7 Care

`care_viewed`

`care_calendar_viewed`

`reminder_create_started`

`reminder_created`

`reminder_completed`

`reminder_snoozed`

`reminder_edited`

`reminder_deleted`

---

# 21.8 Measurements

`measurement_add_started`

`weight_measurement_added`

`temperature_measurement_added`

`measurement_viewed`

`measurement_source_filter_changed`

---

# 21.9 Documents

`documents_viewed`

`document_upload_started`

`document_uploaded`

`document_extraction_started`

`document_extraction_completed`

`document_review_started`

`document_fact_confirmed`

`document_fact_corrected`

`document_fact_rejected`

`document_source_opened`

`document_deleted`

---

# 21.10 Body Check

`body_check_viewed`

`body_check_started`

`body_check_step_completed`

`body_check_capture_added`

`body_check_submitted`

`body_check_completed`

---

# 22. ACCESSIBILITY

All implementation must support:

- TalkBack;
- semantic headings;
- logical focus order;
- 48×48 dp minimum touch targets;
- large font scaling;
- no color-only meaning;
- textual chart descriptions;
- content descriptions for meaningful imagery;
- reduced-motion system preference;
- accessible camera instructions;
- accessible error association.

Pet photos should have useful descriptions where contextually relevant.

Decorative hearts/paws should generally be excluded from accessibility semantics.

---

# 23. LOCALIZATION

All strings must use Android string resources.

Never hard-code Spanish/English inside Composables.

PETi must support:

- locale-aware date;
- locale-aware time;
- localized units;
- °C/°F;
- kg/lb display preferences;
- original-source units retained for documented values.

Layout must tolerate long translations.

---

# 24. STABLE UI TEST IDENTIFIERS

Every screen root:

`screen_UI_xxx_name`

Examples:

`screen_UI_020_home`

`screen_UI_030_analyze`

`screen_UI_047_analysis_result`

`screen_UI_060_timeline`

`screen_UI_070_care`

`screen_UI_080_pet_profile`

Important actions:

`action_continue_google`

`action_add_pet`

`action_switch_pet`

`action_start_initial_scan`

`action_analyze_video`

`action_watch_ad_for_credits`

`action_analysis_submit`

`action_analysis_retry`

`action_add_measurement`

`action_add_document`

`action_fact_confirm`

`action_reminder_complete`

`action_body_check_start`

Do not make UI tests depend on translated labels.

---

# 25. GOLDEN/SCREENSHOT TEST SET

At minimum capture:

- Welcome;
- Sign in;
- My Pets;
- Add Pet;
- Home new-user;
- Home populated;
- Analyze;
- Funding required;
- rewarded verification;
- capture;
- processing;
- result normal;
- result urgent;
- insufficient evidence;
- Timeline;
- Timeline detail;
- Care;
- Calendar;
- Body Check;
- Profile;
- Measurements;
- Documents;
- Document review;
- Settings.

For each important screen also test:

- large fonts;
- long pet name;
- long localized text;
- empty state;
- error state;
- offline state where applicable.

---

# 26. CANONICAL CUSTOMER JOURNEY

A first-time user should experience:

`Welcome`

→ `Google Sign-In`

→ `Legal/AI disclosure`

→ `Add Pet`

→ optional `Initial Scan`

→ `Home`

No mandatory subscription.

No advertisement before the user requests an expensive cloud operation.

---

# 27. FIRST AI JOURNEY

`Analyze`

→ select capability

→ capture/select media

→ provide required context

→ cost/funding resolution

→ if already funded: submit

or:

→ rewarded-ad offer

→ explicit acceptance

→ ad

→ server reward verification

→ Cloud Credits

→ submit

→ upload

→ queued

→ processing

→ validation

→ result

→ Timeline

---

# 28. CORE NON-AI JOURNEY

`Home`

→ `Care`

→ create reminder

→ complete reminder

→ Timeline

No:

- Gemini;
- Cloud Credit;
- advertisement

unless the requested functionality objectively creates a configured costly cloud operation.

---

# 29. DOCUMENT JOURNEY

`Pet`

→ `Records & Documents`

→ `Add document`

→ private upload

If the user only wants storage:

store according to allowance.

If user requests AI extraction:

funding check

→ optional rewarded credit

→ extraction

→ `Review needed`

→ Confirm / Correct / Reject

→ confirmed record

→ Timeline.

---

# 30. VISUAL PRINCIPLE FOR REWARDED FUNDING

The rewarded-ad system must visually feel like a **utility transaction**, not advertising inventory.

Use normal PETi design.

Example:

> **Analyze for free**
>
> This analysis uses cloud AI.
>
> Watch one short ad and receive 3 PETi Cloud Credits.
>
> **Watch ad**
>
> Not now

No banner.

No advertiser logo before the user accepts.

No guilt-based copy.

---

# 31. WHAT SHOULD NEVER APPEAR IN PETi UI

Do not display unsupported:

- “Your pet is healthy”;
- “No disease”;
- “Parasite-free” from stool photo;
- “Periodontal stage” from phone photos;
- “Exact body temperature” from phone sensors;
- literal animal “translation”;
- diagnosis;
- medication dose generated by PETi;
- universal health scores;
- fake activity metrics;
- fake calories;
- fake sleep;
- fake hydration;
- unsupported “ideal weight”;
- sponsored clinical recommendation;
- banner advertising;
- forced interstitial advertising.

---

# 32. IMPLEMENTATION PRIORITY OF THE REFERENCE SCREENS

For a from-scratch build, the reference screens should be implemented in this visual-system order:

## Foundation

1. Welcome.
2. Sign In.
3. My Pets.
4. Add Pet.
5. Home shell.
6. canonical bottom navigation.

## Core useful product

7. Pet Profile.
8. Timeline.
9. Measurements.
10. Care.
11. Calendar.
12. Documents.
13. Settings.

## Cloud operations

14. Analyze Hub.
15. Funding Gate.
16. Reward flow.
17. Capture.
18. Context.
19. Processing.
20. Analysis Result.
21. Analysis Details.

## Advanced flows

22. Assistant.
23. Symptom Summary.
24. Body Check.
25. Document AI extraction/review.
26. Initial Scan.

Specialist Dental and Feces flows should then derive from the same capture/result language rather than creating another visual system.

---

# 33. FINAL UI/UX PRODUCT PRINCIPLE

The final PETi application should visually communicate three things immediately:

### 1. PETi knows what kind of information it is showing

Observed.

Reported.

Measured.

Documented.

Estimated.

Interpreted.

These are never mixed.

### 2. PETi is useful even when it cannot answer

“Not enough evidence” is a normal product state.

“Not enough history” is a normal product state.

“AI isn't available for this species yet” is a normal product state.

### 3. PETi respects the user's attention

The application contains no ambient advertising.

Ordinary navigation remains clean.

When PETi needs the user to help fund an expensive cloud operation, it explains the exchange first and allows the user to choose.

The intended product experience is therefore:

> **A clean premium-feeling pet-care application that happens to be usable for free—not a free app covered in advertising.**

That visual and interaction principle should govern every future PETi screen.