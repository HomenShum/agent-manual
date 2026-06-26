# CLAUDE.md — Project Context

> Context for Claude Code. Read first every session. Decisions below are made —
> build toward them, don't re-open them. Under time pressure, follow BUILD
> SEQUENCE and FALLBACK DISCIPLINE literally. The frontend/backend API is the
> source of truth for the seam between us → see **CONTRACT.md**.
>
> **Status: we are AT the hackathon. All models run on GMI Cloud, not locally.**

---

## What we're building

Upload a product photo → an agent generates an **interactive exploded-parts
diagram** the user can inspect, query, and reassemble.

Pipeline: **image → part-separated 3D model (PartCrafter on GMI) → explodable
viewer → agent that answers questions by acting on the parts.**

The agent *acts*, it doesn't just describe — it explodes, highlights, isolates,
focuses parts via a structured-JSON action protocol the frontend executes live.
The orchestration is the product; the 3D model is raw material.

## Hackathon framing (drives scoring)

- **4-hour build, team of 2.** Scope is the hard constraint. A working
  end-to-end loop beats a pile of half-finished features.
- **Primary track: Agents for Hire** — a real job people outsource: technical
  illustration / exploded parts diagrams / repair & parts-catalog assistance.
- **Secondary track: Marketplace-Ready MVP** — satisfied by deploying the agent
  backend on AgentBox.
- **Win condition:** a judge uploads a photo, watches the agent produce an
  exploded diagram, and asks a question that makes parts move — live, deployed.

## Sponsors — must be incorporated

| Sponsor | Role |
|---|---|
| **GMI Cloud** | (1) Serverless API = agent brain. (2) Dedicated endpoint or rented GPU = **PartCrafter** for image→parts. Both count as "built on GMI." |
| **AgentBox** | Dockerize the Python backend (agent + pipeline), deploy for a live URL, list on marketplace. This IS the Marketplace-Ready track. |
| **Voice Cursor** | Dev-time: code-by-voice during the sprint. Don't bend the architecture around it. |

---

## GMI Cloud — concrete usage

**Agent brain (serverless API — do this FIRST, it's a 10-min integration):**
- OpenAI-compatible REST API. Base URL: `https://api.gmi-serving.com/v1`
- Auth: `Authorization: Bearer <GMI_API_KEY>` on every request.
- Key: console.gmicloud.ai → Organization Settings → create API key.
- Pick a chat model from the console Model Library for JSON-action reasoning.
- Point any OpenAI client at the base URL + key; call chat completions.

**PartCrafter (image→parts) — FORK, resolve this immediately:**
1. **First backend action:** console.gmicloud.ai → Model Library → search
   "PartCrafter" / "part" / "3D".
2. **If in the library:** click Dedicated → confirm GPU + scaling → Deploy → wait
   for "Running" → copy the endpoint URL (the `<>` button). Use that URL. Easiest path.
3. **If NOT in the library:** rent a GMI GPU (H100 on-demand, ~$2/hr, no minimum,
   CUDA 12.x preinstalled) and self-install PartCrafter (deps + weights, wrap in
   FastAPI). ~60–90 min, finicky. Keep the fallback hot.

**Billing note:** dedicated endpoints bill only while "Running" — tear down when done.

---

## Team & ownership

- **Frontend (Next.js, you):** app, Three.js viewer, explode/inspect, upload flow,
  agent chat UI, agent-action execution.
- **Backend (partner):** FastAPI, PartCrafter on GMI, async job queue, GMI agent
  endpoint, storage, AgentBox deploy.
- Boundary + full API: **CONTRACT.md**. Build against the committed fixture so
  neither blocks the other.

## Tech stack (final)

- **Frontend:** Next.js (React) + Three.js (`GLTFLoader`). Deploy to **Vercel**.
  `react-three-fiber` or vanilla Three.js in client components.
- **Backend:** FastAPI + Python. Async job queue (generation ~30s+, must not block).
- **Image→parts:** **PartCrafter on GMI** (dedicated endpoint or rented GPU per the
  fork above). Outputs parts in one global canonical frame.
- **Agent brain:** GMI serverless API (`api.gmi-serving.com/v1`, OpenAI-compatible).
  Vision + structured output. Validate JSON actions against CONTRACT.md schema —
  it's an API contract, not a suggestion.
- **Storage:** local disk for binaries (input image, part GLBs) via static route +
  SQLite/JSON for metadata. Metadata store = the agent's part inventory.
- **Deploy:** frontend → Vercel; backend → AgentBox (Docker). Two deploys over HTTP;
  **CORS required** (allow Vercel domain + localhost).

### Decisions — don't reopen
- **PartCrafter is primary**, because exploded view *requires* part separation,
  which single-mesh models (Hunyuan/Meshy/library 3D) can't do. Those are
  FALLBACKS only — a single fused mesh returned as a one-part result.
- **Single-image input.** No multi-view. "One product photo → exploded diagram."
- **No body/MediaPipe animation.** Interaction is slider + click + agent actions.
- **Next.js on Vercel** for one-command frontend deploy; Python stays on AgentBox.
- **All models on GMI** (sponsor requirement) — nothing runs locally.

---

## Build sequence — follow this order

Each phase ships something that works alone. Parallelize across the 2 of us.

1. **Lock CONTRACT.md + fixture (~15 min, together).** Partner commits
   `fixtures/sample_model.json` + 2–3 sample part GLBs from PartCrafter's HF demo.
2. **In parallel, immediately:**
   - **Partner:** (a) wire GMI serverless API for the agent — checks sponsor box,
     works regardless; (b) run the PartCrafter library search and resolve the fork.
   - **You:** build the viewer against the fixture — render parts assembled,
     explode slider, click-to-inspect.
3. **Working generator (partner).** Get *something* returning a `ModelResult`:
   PartCrafter if its GMI endpoint is up, else a GMI library 3D model / Meshy as a
   one-part result. Frontend swaps fixture URL → real `/api/generate`.
4. **Agent loop (~60 min, TOP PRIORITY, together).** `POST /api/agent`: message +
   model → GMI LLM → validated JSON actions → frontend executes (explode,
   highlight, isolate, focus, reset).
5. **Deploy.** Frontend → Vercel; backend → AgentBox. Fix CORS. Get a live URL.
6. **Demo prep.** Rehearse: upload photo → exploded diagram → one question that
   moves parts.

**Swap PartCrafter in as the upgrade** the moment its GMI endpoint is healthy —
it's the differentiator, not a dependency the demo waits on.

**Stretch only if ahead:** part labels/names, reassemble animation, multi-object,
voice input, better textures.

---

## Fallback discipline ("what does the user get if this step fails?")

- **GMI library 3D model / Meshy single mesh** behind PartCrafter (one-part result;
  explode no-ops, inspect still works). Contract shape never changes.
- **Fixture** behind the live pipeline (frontend never blocked).
- **Typed input** behind voice.
- **Local disk + SQLite** behind cloud storage.

Always ship something explorable.

---

## Gotchas

- **Resolve the PartCrafter fork before sinking time in.** Library-deploy is
  minutes; rent-a-GPU self-install is ~60–90 min. Know which you're on early.
- **PartCrafter is research code** — if self-installing, expect CUDA/dep/weights
  friction. Verify its **license** before pitching "marketplace/commercial."
- **Generation is async (~30s+).** Never block the frontend — always job + poll.
- **CORS** between Vercel and AgentBox is the classic deploy-day blocker. Set it
  early; test cross-origin before the demo.
- **GMI key (401):** header must be exactly `Authorization: Bearer <key>`, no
  whitespace. Regenerate in Org Settings if needed.
- **GMI dedicated endpoint billing** runs while "Running" — tear down after.
- Parts arrive in a **shared canonical frame** — don't re-center parts or explode
  math breaks. Explode = offset from global center (CONTRACT.md).
- **No HTML `<form>`** in React components; use `onClick`/`onChange`.
- AgentBox containers can cycle — anything that must persist can't live only on
  container-local disk.

---

## Env vars

Backend: `GMI_API_KEY`, `GMI_BASE_URL=https://api.gmi-serving.com/v1`,
`PARTCRAFTER_URL`, `MESHY_API_KEY` (fallback).
Frontend: `NEXT_PUBLIC_API_BASE` (AgentBox backend URL).

---

## Pitch reminder

One clean loop on a live URL: photo → exploded parts diagram → ask a question →
parts move in response. Demo the agent doing the job end to end, not breadth.
