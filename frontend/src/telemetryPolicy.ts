export interface FrontendTelemetryEnv {
  VITE_TELEMETRY_ENABLED?: string;
  VITE_SENTRY_DSN?: string;
}

export function isFrontendCloudTelemetryEnabled(env: FrontendTelemetryEnv): boolean {
  return env.VITE_TELEMETRY_ENABLED === 'true'
    && typeof env.VITE_SENTRY_DSN === 'string'
    && env.VITE_SENTRY_DSN.trim().length > 0;
}
