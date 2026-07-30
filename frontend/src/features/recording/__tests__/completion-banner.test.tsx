import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ConfigResponse, FileEntry, FilesResponse } from "@/api/generated/schemas";
import { RecordingCompletionBanner } from "../completion-banner";

// Mock the API/log hooks and the recording store directly so the test does not depend on the
// query client or router runtime.
const { configMock, filesMock, updateMock, deleteMock, mutateMock, addLogMock, storeState } = vi.hoisted(() => ({
  configMock: vi.fn<() => { data: ConfigResponse | undefined }>(() => ({ data: undefined })),
  filesMock: vi.fn<() => { data: FilesResponse | undefined }>(() => ({ data: undefined })),
  updateMock: vi.fn(),
  deleteMock: vi.fn(),
  mutateMock: vi.fn(),
  addLogMock: vi.fn(),
  storeState: {
    finishedRecording: null as { name: string; path: string; durationSec: number } | null,
    dismissFinishedRecording: vi.fn(),
  },
}));

vi.mock("@/hooks/use-api", () => ({
  useConfig: () => configMock(),
  useFiles: () => filesMock(),
  useUpdateRecordingMeta: () => updateMock(),
  useDeleteRecordings: () => deleteMock(),
}));

vi.mock("@/hooks/use-topics-stream", () => ({
  useAddLog: () => addLogMock,
}));

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => vi.fn(),
}));

vi.mock("@/stores/toast-store", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("../store", () => ({
  useRecordingStore: (selector: (s: typeof storeState) => unknown) => selector(storeState),
}));

const TASK_EVAL_FIELD: ConfigResponse["metadata_fields"][number] = {
  key: "task_evaluation",
  label: "Task evaluation",
  type: "select",
  pattern: null,
  placeholder: null,
  options: [
    { value: "success", label: "成功" },
    { value: "failure", label: "失敗" },
  ],
};

function makeConfig(metadata_fields: ConfigResponse["metadata_fields"]): ConfigResponse {
  return {
    ros_domain_id: 0,
    robot_name: "Robot",
    default_topics: [],
    stamp_quality: false,
    upload_enabled: false,
    metadata_fields,
  };
}

function makeEntry(metadata: Record<string, string>): FileEntry {
  return {
    name: "rec_001",
    path: "rec_001",
    size: 0,
    modified_at: 0,
    topic_count: null,
    recording_start_ns: null,
    duration_ns: null,
    message_count: null,
    has_quality_report: false,
    validation_overall_status: null,
    upload_status: null,
    task_name: null,
    recording_config_name: null,
    tags: [],
    metadata,
  };
}

beforeEach(() => {
  storeState.finishedRecording = { name: "rec_001", path: "rec_001", durationSec: 10 };
  configMock.mockReturnValue({ data: makeConfig([TASK_EVAL_FIELD]) });
  filesMock.mockReturnValue({ data: { output_dir: "", entries: [makeEntry({})] } });
  updateMock.mockReturnValue({ mutate: mutateMock, isPending: false });
  deleteMock.mockReturnValue({ mutate: vi.fn(), isPending: false });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("RecordingCompletionBanner", () => {
  it("renders nothing when no recording has finished", () => {
    storeState.finishedRecording = null;
    const { container } = render(<RecordingCompletionBanner />);
    expect(container).toBeEmptyDOMElement();
  });

  it("defaults task evaluation to success and seeds it into the recording", () => {
    render(<RecordingCompletionBanner />);

    // The selector shows the success default...
    expect(screen.getByRole<HTMLSelectElement>("combobox").value).toBe("success");
    // ...and persists it so an untouched banner still labels the take.
    expect(mutateMock).toHaveBeenCalledWith({
      name: "rec_001",
      data: { metadata: { task_evaluation: "success" } },
    });
  });

  it("reflects the already-stored evaluation without re-seeding", () => {
    filesMock.mockReturnValue({ data: { output_dir: "", entries: [makeEntry({ task_evaluation: "failure" })] } });
    render(<RecordingCompletionBanner />);

    expect(screen.getByRole<HTMLSelectElement>("combobox").value).toBe("failure");
    expect(mutateMock).not.toHaveBeenCalled();
  });

  it("saves a changed evaluation, preserving the other metadata", () => {
    filesMock.mockReturnValue({
      data: { output_dir: "", entries: [makeEntry({ operator_id: "007", task_evaluation: "success" })] },
    });
    render(<RecordingCompletionBanner />);

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "failure" } });

    expect(mutateMock).toHaveBeenCalledWith(
      { name: "rec_001", data: { metadata: { operator_id: "007", task_evaluation: "failure" } } },
      expect.objectContaining({ onError: expect.any(Function) }),
    );
  });

  it("renders no evaluation selector when the config has no task_evaluation field", () => {
    configMock.mockReturnValue({ data: makeConfig([]) });
    render(<RecordingCompletionBanner />);

    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(mutateMock).not.toHaveBeenCalled();
  });

  it("cycles the evaluation to the next option on the E key, preserving the other metadata", () => {
    filesMock.mockReturnValue({
      data: { output_dir: "", entries: [makeEntry({ operator_id: "007", task_evaluation: "success" })] },
    });
    render(<RecordingCompletionBanner />);

    fireEvent.keyDown(document, { code: "KeyE" });

    expect(mutateMock).toHaveBeenCalledWith(
      { name: "rec_001", data: { metadata: { operator_id: "007", task_evaluation: "failure" } } },
      expect.objectContaining({ onError: expect.any(Function) }),
    );
  });

  it("wraps the evaluation from the last option back to the first on the E key", () => {
    filesMock.mockReturnValue({ data: { output_dir: "", entries: [makeEntry({ task_evaluation: "failure" })] } });
    render(<RecordingCompletionBanner />);

    fireEvent.keyDown(document, { code: "KeyE" });

    expect(mutateMock).toHaveBeenCalledWith(
      { name: "rec_001", data: { metadata: { task_evaluation: "success" } } },
      expect.objectContaining({ onError: expect.any(Function) }),
    );
  });
});
