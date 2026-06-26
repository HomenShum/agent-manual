/**
 * Placeholder shell. The real UI is laid out in DESIGN_OUTLINE.md and will be
 * generated via Claude Design. The regions below mark the intended layout:
 *
 *   ┌──────────────────────── top navbar ────────────────────────┐
 *   ├──────────────┬─────────────────────────────────────────────┤
 *   │  chat +      │                                             │
 *   │  composer    │            3D model viewer                  │
 *   │  (left)      │            (center, main)                   │
 *   └──────────────┴─────────────────────────────────────────────┘
 *   + assets panel: pops out / overlays from the left edge.
 */
export default function Home() {
  return (
    <main className="flex flex-1 items-center justify-center p-8 text-center">
      <div className="max-w-md">
        <h1 className="text-2xl font-semibold">Parallax</h1>
        <p className="mt-2 text-sm text-neutral-500">
          Repo scaffold ready. UI layout comes next via Claude Design — see{" "}
          <code>DESIGN_OUTLINE.md</code>. Contract types live in{" "}
          <code>lib/contract.ts</code>.
        </p>
      </div>
    </main>
  );
}
