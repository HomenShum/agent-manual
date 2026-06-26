# DESIGN_OUTLINE.md — UI layout (for Claude Design)

> Layout outline only — no visual design committed yet. This is the structural
> brief to hand to Claude Design. The seam to the backend is **CONTRACT.md**;
> the action vocabulary the agent emits is frozen there.

## Screen regions

```
┌──────────────────────────── top navbar ─────────────────────────────────┐
│  Parallax · upload / new · model name · explode slider · (assets toggle) │
├───────────────────┬──────────────────────────────────────────────────────┤
│  CHAT + COMPOSER  │                                                      │
│  (left column,    │              3D MODEL VIEWER                         │
│   persistent)     │              (center, main stage)                    │
│                   │                                                      │
│  - message log    │   - Three.js canvas, assembled by default            │
│  - agent replies  │   - explode driven by slider + agent `explode`       │
│  - composer       │   - click part = inspect; highlight / isolate / focus│
│    (textarea +    │                                                      │
│     send)         │                                                      │
└───────────────────┴──────────────────────────────────────────────────────┘

   ASSETS PANEL  ◀ pops out / overlays from the LEFT edge (toggle in navbar)
   - overlays on top of content (does not push layout)
   - grid/list of generated assets: source image + each generated model/parts
   - selecting an asset loads it into the center viewer
```

## Region notes

**Top navbar** — app identity, primary actions (upload a new photo / start over),
current model label, the explode slider (0→1), and the assets-panel toggle.

**Left column — chat + composer (persistent).** The agent conversation. User asks
a question → agent replies in text → frontend executes the returned `actions`
(`explode`, `highlight`, `isolate`, `focus`, `reset`) against the center viewer.
Composer is a textarea + send (no HTML `<form>` — use onClick/onChange).

**Center — 3D model viewer (main stage).** Three.js canvas. Renders all part GLBs
at native position = assembled. Explode radiates from `result.center` by the
slider `factor`. Click-to-inspect a part. The agent's actions animate this view.

**Assets panel — left popout overlay.** Hidden by default; toggled from the navbar.
Slides in from the left edge and **overlays** the chat/content (it does not reflow
the layout). Shows generated assets — the uploaded source image and each generated
model — so the user can switch between them. Selecting one loads it center.

## States to design

- **Empty / first run:** no model yet → prompt to upload a product photo.
- **Generating:** job queued/running (~30s+) → progress in the viewer area
  (poll `progress` 0–100), chat available but viewer pending.
- **Loaded:** model assembled, slider at 0, chat ready.
- **One-part fallback:** a fused single mesh (parts length 1) — explode is a no-op,
  inspect still works. Design must not break with one part.
- **Error:** generation failed → readable message + retry.

## Constraints carried from CLAUDE.md / CONTRACT.md

- Action vocabulary is frozen: `explode(factor)`, `highlight(part_id)`,
  `isolate(part_ids[])`, `focus(part_id)`, `reset`.
- Frontend owns explode math; never re-center parts.
- Assets/binaries come from the backend under `/files/...`.
