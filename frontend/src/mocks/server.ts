/** MSW server. Combines orval-generated handlers. */
import { setupServer } from "msw/node";
import { getConfigMock } from "@/api/generated/config/config.msw";
import { getRecordingMock } from "@/api/generated/recording/recording.msw";
import { getRecordingsMock } from "@/api/generated/recordings/recordings.msw";
import { getTopicsMock } from "@/api/generated/topics/topics.msw";

export const server = setupServer(
  ...getRecordingMock(),
  ...getTopicsMock(),
  ...getConfigMock(),
  ...getRecordingsMock(),
);
