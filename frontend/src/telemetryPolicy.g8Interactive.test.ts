import { describe, expect, it } from 'vitest';
import { isFrontendCloudTelemetryEnabled } from './telemetryPolicy';

describe('frontend cloud telemetry opt-in contract', () => {
  it('fails closed when a Sentry DSN exists without explicit opt-in', () => {
    expect(isFrontendCloudTelemetryEnabled({
      VITE_SENTRY_DSN: 'https://example.invalid/123',
    })).toBe(false);
  });

  it('accepts only the exact explicit true opt-in', () => {
    for (const value of ['', 'false', '1', 'TRUE', 'yes']) {
      expect(isFrontendCloudTelemetryEnabled({
        VITE_TELEMETRY_ENABLED: value,
        VITE_SENTRY_DSN: 'https://example.invalid/123',
      })).toBe(false);
    }
  });

  it('stays disabled when opt-in is true but the DSN is absent or blank', () => {
    expect(isFrontendCloudTelemetryEnabled({ VITE_TELEMETRY_ENABLED: 'true' })).toBe(false);
    expect(isFrontendCloudTelemetryEnabled({
      VITE_TELEMETRY_ENABLED: 'true',
      VITE_SENTRY_DSN: '   ',
    })).toBe(false);
  });

  it('enables cloud telemetry only when opt-in and a non-empty DSN are both present', () => {
    expect(isFrontendCloudTelemetryEnabled({
      VITE_TELEMETRY_ENABLED: 'true',
      VITE_SENTRY_DSN: 'https://example.invalid/123',
    })).toBe(true);
  });
});
