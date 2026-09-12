import { describe, expect, it } from 'vitest';
import {
  clearDocumentAuthorPractitionerId,
  getDocumentAuthorPractitionerId,
  installDocumentAuthorRequestGuard,
  setDocumentAuthorPractitionerId,
} from './DocumentAuthorSelection';

function fakeClient() {
  let handler: ((config: any) => any) | null = null;
  let ejected: number | null = null;
  return {
    client: {
      interceptors: {
        request: {
          use: (next: (config: any) => any) => {
            handler = next;
            return 17;
          },
          eject: (id: number) => {
            ejected = id;
          },
        },
      },
    },
    run: (config: any) => {
      if (!handler) throw new Error('interceptor not installed');
      return handler(config);
    },
    ejected: () => ejected,
  };
}

describe('P3 document author selection guard', () => {
  it('stores and clears the selected practitioner explicitly', () => {
    clearDocumentAuthorPractitionerId();
    expect(getDocumentAuthorPractitionerId()).toBeNull();
    setDocumentAuthorPractitionerId(42);
    expect(getDocumentAuthorPractitionerId()).toBe(42);
    clearDocumentAuthorPractitionerId();
    expect(getDocumentAuthorPractitionerId()).toBeNull();
  });

  it('injects the author only into document generation POST payloads', () => {
    const fake = fakeClient();
    setDocumentAuthorPractitionerId(42);
    const uninstall = installDocumentAuthorRequestGuard(fake.client);

    const generation = fake.run({
      method: 'post',
      url: '/documents/generate?archive=true',
      data: { type: 'ordonnance', patient_id: 101 },
    });
    expect(generation.data).toEqual({
      type: 'ordonnance',
      patient_id: 101,
      author_practitioner_id: 42,
    });

    const unrelated = fake.run({
      method: 'post',
      url: '/patients/101/practitioner',
      data: { practitioner_id: 9 },
    });
    expect(unrelated.data).toEqual({ practitioner_id: 9 });

    const read = fake.run({ method: 'get', url: '/documents/generate', data: undefined });
    expect(read.data).toBeUndefined();

    uninstall();
    expect(fake.ejected()).toBe(17);
    clearDocumentAuthorPractitionerId();
  });

  it('leaves generation payload untouched when no author is selected', () => {
    const fake = fakeClient();
    clearDocumentAuthorPractitionerId();
    installDocumentAuthorRequestGuard(fake.client);

    const generation = fake.run({
      method: 'post',
      url: '/documents/generate',
      data: { type: 'certificat', patient_id: 101 },
    });
    expect(generation.data).toEqual({ type: 'certificat', patient_id: 101 });
  });
});
