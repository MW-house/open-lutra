import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { TopicQuality } from "@/api/generated/schemas";
import { TopicDetails } from "../ui/topic-details";
import { TopicQualityRow } from "../ui/topic-quality-row";

function makeTopic(overrides: Partial<TopicQuality> = {}): TopicQuality {
  return {
    name: "/test/topic",
    msg_type: "std_msgs/Float64",
    message_count: 100,
    actual_frequency_hz: 30,
    status: "warning",
    loss_count: 2,
    minor_loss_count: 2,
    major_loss_count: 0,
    start_delay_sec: 0,
    end_early_sec: 0,
    size_stats: {
      min_bytes: 100,
      max_bytes: 200,
      avg_bytes: 150,
      std_bytes: 10,
      zero_size_count: 0,
    },
    loss_events: [
      { timestamp_sec: 1.5, duration_sec: 0.1, lost_count: 1, severity: "minor" },
      { timestamp_sec: 3.2, duration_sec: 0.2, lost_count: 2, severity: "minor" },
    ],
    ...overrides,
  } as TopicQuality;
}

describe("TopicDetails", () => {
  it("shows the loss-event list by default", () => {
    render(<TopicDetails topic={makeTopic()} recordingDuration={10} />);
    expect(screen.getByText(/0\.100s/)).toBeInTheDocument();
    expect(screen.getByText(/0\.200s/)).toBeInTheDocument();
  });

  it("hides the loss-event list when lossExpanded=false", () => {
    render(<TopicDetails topic={makeTopic()} recordingDuration={10} lossExpanded={false} />);
    expect(screen.queryByText(/0\.100s/)).not.toBeInTheDocument();
    expect(screen.queryByText(/0\.200s/)).not.toBeInTheDocument();
  });
});

describe("TopicQualityRow chevron toggle", () => {
  it("toggles the loss-event list on chevron click while forceExpanded", () => {
    const onTopicClick = vi.fn();
    render(<TopicQualityRow topic={makeTopic()} recordingDuration={10} forceExpanded onTopicClick={onTopicClick} />);

    // Initial state: loss events hidden
    expect(screen.queryByText(/0\.100s/)).not.toBeInTheDocument();

    // Chevron click: expand, and the row click (onTopicClick) does not fire
    fireEvent.click(screen.getByRole("button", { name: /Expand/ }));
    expect(screen.getByText(/0\.100s/)).toBeInTheDocument();
    expect(onTopicClick).not.toHaveBeenCalled();

    // Click again to collapse
    fireEvent.click(screen.getByRole("button", { name: /Collapse/ }));
    expect(screen.queryByText(/0\.100s/)).not.toBeInTheDocument();
  });

  it("collapses the whole row on chevron click when forceExpanded is absent", () => {
    render(<TopicQualityRow topic={makeTopic()} recordingDuration={10} />);

    // Initially collapsed (details hidden)
    expect(screen.queryByText(/0\.100s/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Expand/ }));
    expect(screen.getByText(/0\.100s/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Collapse/ }));
    expect(screen.queryByText(/0\.100s/)).not.toBeInTheDocument();
  });

  it("clicking the row (anywhere but the chevron) fires onTopicClick", () => {
    const onTopicClick = vi.fn();
    render(<TopicQualityRow topic={makeTopic()} recordingDuration={10} forceExpanded onTopicClick={onTopicClick} />);
    fireEvent.click(screen.getByText(/test\/topic/));
    expect(onTopicClick).toHaveBeenCalledWith("/test/topic");
  });
});
