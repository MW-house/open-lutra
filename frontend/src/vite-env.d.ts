/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Developer UI display flag, set when launched via `make dev-up` ("true" | undefined). */
  readonly VITE_DEV_MODE?: string;
  /**
   * Absolute API origin (e.g. "http://localhost:8000") used to bypass the Vite dev-server proxy
   * for long-lived endpoints (MJPEG streams). Unset in production so requests stay same-origin.
   */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
