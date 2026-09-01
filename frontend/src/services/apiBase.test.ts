import { describe, expect, it } from 'vitest';
import { resolveApiBase } from './apiBase';

describe('resolveApiBase', () => {
  it('ignores an HTTP override when the page is HTTPS', () => {
    expect(resolveApiBase('http://127.0.0.1:8005', {
      protocol: 'https:',
      hostname: '127.0.0.1',
    })).toBe('https://127.0.0.1:8005');
  });

  it('derives the cabinet hostname for an HTTPS mobile page', () => {
    expect(resolveApiBase('http://127.0.0.1:8005', {
      protocol: 'https:',
      hostname: 'digitalcrown.local',
    })).toBe('https://digitalcrown.local:8005');
  });

  it('keeps an explicit HTTPS override', () => {
    expect(resolveApiBase('https://digitalcrown.local:8005/', {
      protocol: 'https:',
      hostname: '127.0.0.1',
    })).toBe('https://digitalcrown.local:8005');
  });

  it('keeps the HTTP dev override on an HTTP page', () => {
    expect(resolveApiBase('http://127.0.0.1:8005', {
      protocol: 'http:',
      hostname: 'localhost',
    })).toBe('http://127.0.0.1:8005');
  });
});
