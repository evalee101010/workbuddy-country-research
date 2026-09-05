---
name: workbuddy-country-research
description: "Collect, validate, and package one country's public WorkBuddy/Cowork competitor feedback, local work needs, and KOL/KOC content signals. Use for country-level collection, resuming a run, internal structural validation, ZIP handoff, or merging country packs; do not use for market synthesis, scoring, policy conclusions, or product strategy."
---

# WorkBuddy Country Research

Produce a complete, mergeable, internal-use country data package. Preserve raw public evidence and provenance. Do not produce country insights, opportunity rankings, policy conclusions, or product recommendations during this workflow.

## Start a country run

Collect or infer only these run parameters:

- country name or ISO2 code;
- researcher name;
- research window end date;
- optional start date and run ID.

Use ISO2 directory names. Default the start date to the bundled country configuration and the run ID to `<YYYY-MM-DD>-<iso2>-public-signals`. Run commands from the researcher's chosen workspace root; never write results into this Skill directory.

Resolve every `./scripts/...` path below relative to this `SKILL.md`, while keeping the command working directory set to the research workspace. The scripts themselves must not be copied into each country run.

Before collection, read [research-protocol.md](references/research-protocol.md) and [country-channel-adaptation.md](references/country-channel-adaptation.md). Then initialize and discover:

```bash
./scripts/workbuddy-country-runner init DE --run-id 2026-09-04-de-public-signals --researcher Anna --window-end 2026-09-04
./scripts/workbuddy-country-runner discover DE --run-id 2026-09-04-de-public-signals
```

The scripts create a private runtime under `<workspace>/.workbuddy-country-research/` and research output under `<workspace>/research/runs/`. If a country config is absent, stop after preparing a draft with the country adaptation reference. Confirm its language, geography, audience, product, and channel assumptions with the researcher before discovery.

## Adapt sources before collecting

Treat bundled channels as candidates, never as approved universal sources. Pilot locally appropriate public channels and complete:

- `02-source-discovery.csv`;
- `03-channel-fit-pilot.csv`;
- `04-approved-source-plan.yml` (legacy filename; it is the internal source plan, not a manager gate).

Assign each source `Core`, `Supplement`, `Discovery-only`, `Auth-optional`, `Consent-required`, or `Reject`, with a reason. Never make GitHub or a developer-heavy community the sole country Core. A stream may have no Core only when its `documented_gap` is explicit.

Use `pilot` to regenerate role suggestions after pilot counts are recorded. For this internal workflow, `source_plan_pending` is not a request for manager approval; the executor owns the recorded source decision.

## Collect A/B/C evidence

Read [evidence-field-contract.md](references/evidence-field-contract.md) before writing records.

- A: real feedback about Cowork and comparable products in concrete work tasks;
- B: local work tasks, pain points, current solutions, desired outcomes, and payment/switching signals;
- C: KOL/KOC task content, visible engagement, hook, format, CTA, offer, and funnel stage.

Execute every pre-registered core-language query row and record zero hits and access failures. Add country-adapted incremental queries in batches. Keep one unique public item per `content_id` in raw, then link one or more independently judgeable evidence records through `content_id`. Preserve the shortest necessary original quotation, Chinese translation, URL, date, query ID, and explicit country evidence.

Stop only after the required matrix is recorded and two consecutive incremental batches add neither qualified unique content nor a new task/audience/key counterexample. Otherwise label the run `budget_limited`, `access_limited`, or `ranking_limited`. These labels describe the search frame and never imply population representativeness.

## Validate and hand off

Run deterministic internal validation at any time:

```bash
./scripts/validate-country-run DE --run-id 2026-09-04-de-public-signals
```

Fix every `BLOCK`. `WARN` is allowed for internal exploration and must remain visible in the package. There is no Gate B signature in this path.

Before packaging, read [package-handoff-contract.md](references/package-handoff-contract.md). Create the only required coworker deliverable:

```bash
./scripts/package-country-run DE --run-id 2026-09-04-de-public-signals
```

Return the resulting `workbuddy-country-data-<ISO2>-<run-id>.zip`, not a manually rearranged folder and not a narrative report.

To combine two or more received country ZIPs without deleting cross-country duplicates:

```bash
./scripts/merge-country-packs --output-dir research/merged/2026-09-public-signals country-a.zip country-b.zip
```

## Non-negotiable boundaries

- Use only publicly accessible material or explicitly authorized access; never bypass login, rate limits, robots restrictions, or private-group consent.
- Do not infer residence, occupation, audience geography, price, clicks, income, or effectiveness when not public.
- Do not store private phone numbers, email addresses, or unnecessary personal identifiers.
- Do not silently drop zero-hit queries, failed channels, unresolved geography, excluded rows, or cross-country duplicates.
- Do not call the result representative, exhaustive of a platform, or a market-size estimate.
- Do not alter schema headers or reuse another country's IDs.
