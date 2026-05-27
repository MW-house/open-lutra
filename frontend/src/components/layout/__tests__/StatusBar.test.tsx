import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { JobSchema, MemoryInfo } from "@/api/generated/schemas";
import { StatusBar } from "../StatusBar";

// Mock all hooks the StatusBar reads so the test can drive state directly.
// `vi.hoisted` keeps the mock function references valid through hoisting.
const { useMemoryMock, useIsRecordingMock, useConnectionStatusMock, useJobsMock } = vi.hoisted(() => ({
  useMemoryMock: vi.fn<() => { data: MemoryInfo | undefined }>(() => ({ data: undefined })),
  useIsRecordingMock: vi.fn<() => boolean>(() => false),
  useConnectionStatusMock: vi.fn<() => "connected" | "disconnected">(() => "connected"),
  useJobsMock: vi.fn<() => JobSchema[]>(() => []),
}));

vi.mock("@/hooks/use-api", () => ({
  useMemory: () => useMemoryMock(),
  useIsRecording: () => useIsRecordingMock(),
}));
vi.mock("@/hooks/use-topics-stream", () => ({
  useConnectionStatus: () => useConnectionStatusMock(),
}));
vi.mock("@/hooks/use-jobs-stream", () => ({
  useJobs: () => useJobsMock(),
}));
vi.mock("@/stores/panel-store", () => ({
  usePanelStore: (selector: (state: { showQueryDevtools: boolean; toggleQueryDevtools: () => void }) => unknown) =>
    selector({ showQueryDevtools: false, toggleQueryDevtools: () => undefined }),
}));

function makeJob(overrides: Partial<JobSchema>): JobSchema {
  return {
    job_id: "j1",
    type: "validation",
    folder: "rec_001",
    status: "running",
    progress: { step: "", step_label: "", current: 0, total: 1 },
    error: null,
    created_at: "2026-05-25T00:00:00",
    started_at: null,
    finished_at: null,
    ...overrides,
  };
}

beforeEach(() => {
  useMemoryMock.mockReturnValue({ data: undefined });
  useIsRecordingMock.mockReturnValue(false);
  useConnectionStatusMock.mockReturnValue("connected");
  useJobsMock.mockReturnValue([]);
});

afterEach(() => {
  useMemoryMock.mockReset();
  useIsRecordingMock.mockReset();
  useConnectionStatusMock.mockReset();
  useJobsMock.mockReset();
});

describe("StatusBar jobs display", () => {
  it("renders pills for queued and running jobs (including validation)", () => {
    useJobsMock.mockReturnValue([
      makeJob({ job_id: "j1", type: "validation", status: "running" }),
      makeJob({ job_id: "j2", type: "quality", status: "queued" }),
    ]);
    render(<StatusBar />);
    expect(screen.getByText("Validation")).toBeInTheDocument();
    expect(screen.getByText("Quality")).toBeInTheDocument();
  });

  it("filters out completed and failed jobs", () => {
    useJobsMock.mockReturnValue([
      makeJob({ job_id: "j1", type: "validation", status: "completed" }),
      makeJob({ job_id: "j2", type: "media", status: "failed" }),
    ]);
    render(<StatusBar />);
    expect(screen.queryByText("Validation")).not.toBeInTheDocument();
    expect(screen.queryByText("Media")).not.toBeInTheDocument();
  });

  it("still renders the connection-status label when no jobs are active", () => {
    render(<StatusBar />);
    expect(screen.getByText("Connected")).toBeInTheDocument();
  });

  it("shows the memory readout when used_bytes > 0", () => {
    useMemoryMock.mockReturnValue({ data: { used_bytes: 1024 * 1024 * 200, limit_bytes: 1024 * 1024 * 1024 } });
    render(<StatusBar />);
    expect(screen.getByText(/200MB/)).toBeInTheDocument();
    expect(screen.getByText(/1024MB/)).toBeInTheDocument();
  });

  it("renders the REC badge while recording", () => {
    useIsRecordingMock.mockReturnValue(true);
    render(<StatusBar />);
    expect(screen.getByText("REC")).toBeInTheDocument();
  });
});
