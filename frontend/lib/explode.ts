/**
 * Explode math (frontend-owned, per CONTRACT.md).
 *
 *   dir    = normalize(part.centroid − result.center)
 *   offset = dir * factor * EXPLODE_SCALE
 *   part.position = part.centroid + offset
 *
 * factor = 0 → assembled. factor = 1 → fully exploded.
 */
import type { BBox, ModelResult, Part, Vec3 } from "./contract";

/** Bounding-box diagonal length — a sane default for EXPLODE_SCALE. */
export function bboxDiagonal(bbox: BBox): number {
  const dx = bbox.max[0] - bbox.min[0];
  const dy = bbox.max[1] - bbox.min[1];
  const dz = bbox.max[2] - bbox.min[2];
  return Math.hypot(dx, dy, dz);
}

/** World position for a part at a given explode factor. */
export function explodedPosition(
  part: Part,
  center: Vec3,
  factor: number,
  explodeScale: number,
): Vec3 {
  const dir: Vec3 = [
    part.centroid[0] - center[0],
    part.centroid[1] - center[1],
    part.centroid[2] - center[2],
  ];
  const len = Math.hypot(dir[0], dir[1], dir[2]) || 1;
  const mag = (factor * explodeScale) / len;
  return [
    part.centroid[0] + dir[0] * mag,
    part.centroid[1] + dir[1] * mag,
    part.centroid[2] + dir[2] * mag,
  ];
}

/** Convenience: default explode scale for a result (≈ bbox diagonal). */
export function explodeScaleFor(result: ModelResult): number {
  return bboxDiagonal(result.bbox) || 1;
}
