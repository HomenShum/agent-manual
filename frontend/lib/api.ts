/**
 * Thin client for the backend API (see CONTRACT.md).
 * Base URL comes from NEXT_PUBLIC_API_BASE (the AgentBox URL).
 */
import type { AgentRequest, AgentResponse, Job } from "./contract";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

function url(path: string): string {
  return `${API_BASE}${path}`;
}

/** Resolve a (possibly relative) /files URL against the backend base. */
export function fileUrl(modelUrl: string): string {
  if (/^https?:\/\//.test(modelUrl)) return modelUrl;
  return url(modelUrl);
}

/** Kick off generation. Returns the queued job. */
export async function startGenerate(image: File): Promise<Job> {
  const body = new FormData();
  body.append("image", image);
  const res = await fetch(url("/api/generate"), { method: "POST", body });
  if (!res.ok) throw new Error(`generate failed: ${res.status}`);
  return res.json();
}

/** Fetch a job's current state. */
export async function getJob(jobId: string): Promise<Job> {
  const res = await fetch(url(`/api/jobs/${jobId}`), { cache: "no-store" });
  if (!res.ok) throw new Error(`job fetch failed: ${res.status}`);
  return res.json();
}

/**
 * Poll a job every `intervalMs` until it is `done` or `error`.
 * `onProgress` fires on each tick. Resolves with the terminal job.
 */
export async function pollJob(
  jobId: string,
  onProgress?: (job: Job) => void,
  intervalMs = 1500,
): Promise<Job> {
  for (;;) {
    const job = await getJob(jobId);
    onProgress?.(job);
    if (job.status === "done" || job.status === "error") return job;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}

/** Ask the agent. Returns reply + ordered actions for the viewer to execute. */
export async function askAgent(req: AgentRequest): Promise<AgentResponse> {
  const res = await fetch(url("/api/agent"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`agent failed: ${res.status}`);
  return res.json();
}
