import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../../../services/api';
import { usePatientStore } from '../../../stores/usePatientStore';
import { useAuthStore } from '../../../stores/useAuthStore';
import type { Patient } from '../../../types';
import { cn } from '../../../utils/cn';
import { hasAccess } from '../../../utils/accessControl';

type PatientAvatarProps = {
  patientId: number | string;
  firstName?: string | null;
  lastName?: string | null;
  fullName?: string | null;
  photoUrl?: string | null;
  resolveFromDirectory?: boolean;
  className?: string;
  imageClassName?: string;
  initialsClassName?: string;
};

let patientDirectoryRequest: Promise<Patient[]> | null = null;

const canonicalPhotoUrl = (patientId: number | string) => `/api/patients/${patientId}/photo`;

function isCanonicalPhotoUrl(patientId: number | string, value?: string | null) {
  return value === canonicalPhotoUrl(patientId);
}

async function ensurePatientDirectory(): Promise<Patient[]> {
  const state = usePatientStore.getState();
  if (state.patientsCacheLoaded) return state.patientsCache;

  if (!patientDirectoryRequest) {
    patientDirectoryRequest = api.get('/patients/')
      .then(response => {
        const patients = Array.isArray(response.data) ? response.data as Patient[] : [];
        usePatientStore.getState().setPatientsCache(patients);
        return patients;
      })
      .finally(() => {
        patientDirectoryRequest = null;
      });
  }
  return patientDirectoryRequest;
}

export function PatientAvatar({
  patientId,
  firstName,
  lastName,
  fullName,
  photoUrl,
  resolveFromDirectory = false,
  className,
  imageClassName,
  initialsClassName,
}: PatientAvatarProps) {
  const user = useAuthStore(state => state.user);
  const canReadPatientMedia = hasAccess(user, 'patients');
  const [resolvedPhotoUrl, setResolvedPhotoUrl] = useState<string | null>(() =>
    canReadPatientMedia && isCanonicalPhotoUrl(patientId, photoUrl) ? photoUrl! : null,
  );
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const blobUrlRef = useRef<string | null>(null);

  const initials = useMemo(() => {
    if (fullName?.trim()) {
      const parts = fullName.trim().split(/\s+/);
      const first = parts[0]?.charAt(0) || '';
      const last = parts.length > 1 ? parts[parts.length - 1]?.charAt(0) || '' : '';
      return (first + last).toUpperCase() || 'P';
    }
    const first = (firstName || '').trim().charAt(0);
    const last = (lastName || '').trim().charAt(0);
    return (first + last).toUpperCase() || 'P';
  }, [firstName, fullName, lastName]);

  useEffect(() => {
    let cancelled = false;

    if (!canReadPatientMedia) {
      setResolvedPhotoUrl(null);
      return () => { cancelled = true; };
    }

    if (photoUrl !== undefined) {
      setResolvedPhotoUrl(isCanonicalPhotoUrl(patientId, photoUrl) ? photoUrl! : null);
      return () => { cancelled = true; };
    }

    if (!resolveFromDirectory) {
      setResolvedPhotoUrl(null);
      return () => { cancelled = true; };
    }

    const cached = usePatientStore.getState().patientsCache.find(patient => patient.id === Number(patientId));
    if (cached) {
      setResolvedPhotoUrl(isCanonicalPhotoUrl(patientId, cached.photo_url) ? cached.photo_url! : null);
      return () => { cancelled = true; };
    }

    ensurePatientDirectory()
      .then(patients => {
        if (cancelled) return;
        const patient = patients.find(item => item.id === Number(patientId));
        setResolvedPhotoUrl(isCanonicalPhotoUrl(patientId, patient?.photo_url) ? patient!.photo_url! : null);
      })
      .catch(() => {
        if (!cancelled) setResolvedPhotoUrl(null);
      });

    return () => { cancelled = true; };
  }, [canReadPatientMedia, patientId, photoUrl, resolveFromDirectory]);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    const revokeCurrent = () => {
      if (blobUrlRef.current?.startsWith('blob:')) URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
      setBlobUrl(null);
    };

    revokeCurrent();
    if (!canReadPatientMedia || !resolvedPhotoUrl || !isCanonicalPhotoUrl(patientId, resolvedPhotoUrl)) {
      return () => {
        cancelled = true;
        controller.abort();
      };
    }

    api.get(`/patients/${patientId}/photo`, {
      responseType: 'blob',
      signal: controller.signal,
    })
      .then(response => {
        const next = URL.createObjectURL(response.data);
        if (cancelled) {
          URL.revokeObjectURL(next);
          return;
        }
        if (blobUrlRef.current?.startsWith('blob:')) URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = next;
        setBlobUrl(next);
      })
      .catch(() => {
        if (!cancelled) revokeCurrent();
      });

    return () => {
      cancelled = true;
      controller.abort();
      if (blobUrlRef.current?.startsWith('blob:')) URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    };
  }, [canReadPatientMedia, patientId, resolvedPhotoUrl]);

  return (
    <span
      data-patient-avatar
      data-photo-state={blobUrl ? 'photo' : 'initials'}
      className={cn(
        'relative shrink-0 overflow-hidden bg-primary/10 text-primary flex items-center justify-center font-black',
        className,
      )}
      aria-label={blobUrl ? `Photo de ${fullName || `${firstName || ''} ${lastName || ''}`}`.trim() : 'Initiales du patient'}
    >
      {blobUrl ? (
        <img
          src={blobUrl}
          alt=""
          aria-hidden="true"
          className={cn('h-full w-full object-cover', imageClassName)}
        />
      ) : (
        <span className={initialsClassName}>{initials}</span>
      )}
    </span>
  );
}
