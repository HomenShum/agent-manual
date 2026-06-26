# CONTRACT.md — The Seam Between Us

> **Jointly owned. Neither person changes it alone.** It is the API between
> frontend and backend. Lock it in the first 15 minutes, then we both build
> full-speed without blocking. If reality forces a change, we change it *together*
> and both update our code.

---

## Who owns what

| | **Frontend (you — Next.js)** | **Backend (partner — Python on GMI/AgentBox)** |
|---|---|---|
| Owns | Next.js app, Three.js viewer, explode/inspect interaction, upload flow, agent chat UI, executing agent `actions` | FastAPI, PartCrafter on GMI, GMI agent endpoint, async job queue, storage, AgentBox deploy |
| Deliverable | "Given the result shape below, a site that explodes, inspects, and queries the model" | "A URL that returns parts as GLBs + metadata in the shape below" |

**Boundary:** backend produces data, frontend displays/interacts. Where the models
actually run (GMI serverless API, GMI dedicated endpoint, rented GMI GPU) is a
backend-internal detail the frontend never sees. Frontend only knows
`NEXT_PUBLIC_API_BASE`.

---

## Base URL & conventions

- Frontend → backend base URL: `NEXT_PUBLIC_API_BASE` (the AgentBox URL).
- Backend internal env (frontend never touches): `GMI_API_KEY`,
  `GMI_BASE_URL=https://api.gmi-serving.com/v1`, `PARTCRAFTER_URL` (GMI endpoint),
  `MESHY_API_KEY` (fallback).
- GLB/image files served from backend under `/files/...` with **CORS enabled**
  (Vercel + localhost:3000 origins).
- Optional: proxy backend calls through Next.js API routes (`/app/api/*`) to dodge
  CORS and hide keys. Backend doesn't care either way.
- All coordinates are in PartCrafter's **global canonical frame** — parts come
  pre-assembled. Frontend computes the explosion; backend never does.

---

## 1. Generate (async — generation takes ~30s+, cannot block)

```
POST {API_BASE}/api/generate          multipart/form-data: image=<file>
  → 202 { "job_id": "uuid", "status": "queued" }

GET  {API_BASE}/api/jobs/{job_id}
  → 200 {
      "job_id": "uuid",
      "status": "queued" | "running" | "done" | "error",
      "progress": 0,                       // 0–100, best effort
      "result": <ModelResult> | null,      // present only when status == "done"
      "error":  null | "human-readable string"
    }
```
Frontend polls `GET /api/jobs/{id}` every ~1.5s until `done` or `error`.

## 2. ModelResult (the heart of the contract)

```jsonc
{
  "model_id": "uuid",
  "source_image_url": "/files/<model_id>/input.png",
  "center": [x, y, z],                 // global center; explode radiates from here
  "bbox":   { "min": [x,y,z], "max": [x,y,z] },
  "parts": [
    {
      "part_id":   "p0",
      "label":     "housing",          // fallback "part_0" if PartCrafter gives no name
      "model_url": "/files/<model_id>/p0.glb",
      "centroid":  [x, y, z],          // part center, same canonical frame
      "bbox":      { "min": [x,y,z], "max": [x,y,z] }
    }
    // ...one entry per part, arbitrary count
  ]
}
```
**Guarantee the frontend relies on:** every part GLB is positioned in the same
frame, so loading them all at native position renders the assembled object.
`center` + each `centroid` are all the frontend needs to explode.

## 3. Agent (Ironbook-style action protocol, applied to parts)

```jsonc
POST {API_BASE}/api/agent
  {
    "model_id": "uuid",
    "message": "which part is the filter?",
    "explode_factor": 0.4               // current viewer state, so agent has context
  }
  → 200 {
      "reply": "The filter is the cylindrical part near the intake.",
      "actions": [                       // frontend executes these in order
        { "type": "explode",   "factor": 0.7 },
        { "type": "highlight", "part_id": "p3" },
        { "type": "isolate",   "part_ids": ["p3"] },
        { "type": "focus",     "part_id": "p3" },
        { "type": "reset" }
      ]
    }
```

**Action vocabulary (frozen — both sides implement exactly these):**
| type | fields | frontend behavior |
|---|---|---|
| `explode` | `factor` 0–1 | set explode slider to factor |
| `highlight` | `part_id` | emphasize one part (color/outline) |
| `isolate` | `part_ids[]` | show only these parts |
| `focus` | `part_id` | move camera to frame this part |
| `reset` | — | assembled, all parts visible, camera home |

Backend validates the GMI LLM's output against this schema before returning.
Unknown action types are dropped, not passed through.

---

## Explode math (frontend-owned, documented so we agree)

For each part, with slider `factor` ∈ [0,1]:
```
dir    = normalize(part.centroid − result.center)
offset = dir * factor * EXPLODE_SCALE     // EXPLODE_SCALE ~ bbox diagonal
part.position = part.centroid + offset
```
`factor = 0` → assembled. `factor = 1` → fully exploded. The agent's `explode`
action just sets this same `factor`.

---

## The unblock trick — DO THIS AT MINUTE 15

**Partner commits a fixture before PartCrafter on GMI is confirmed working:**
- `fixtures/sample_model.json` — a real `ModelResult` in the shape above
- 2–3 sample part GLBs (grab from PartCrafter's Hugging Face demo output)
- serve them statically at the same `/files/...` paths

Frontend builds the **entire** app — viewer, explode, inspect, agent UI — against
the fixture. When the real GMI pipeline lands, it's a **one-URL swap**. Neither
person waits on the other's hardest task.

---

## Status / error discipline

- Every job ends `done` or `error` — never hangs. On failure, backend sets `error`
  with a readable message; frontend shows it and offers retry.
- **Fallback:** if PartCrafter on GMI isn't ready/working, backend returns a
  single fused mesh (a GMI library 3D model, or Meshy) as a **one-part**
  `ModelResult` (`parts` length 1). Frontend handles a one-part result gracefully
  (explode is a no-op, inspect still works). The contract shape never changes —
  only the number of parts.
