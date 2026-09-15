import { getApps, initializeApp, type FirebaseApp } from 'firebase/app';
import {
  browserSessionPersistence,
  createUserWithEmailAndPassword,
  getAuth,
  inMemoryPersistence,
  onAuthStateChanged,
  reload,
  sendEmailVerification,
  setPersistence,
  signInWithEmailAndPassword,
  signOut,
  type Auth,
  type User,
} from 'firebase/auth';

const PATIENT_FIREBASE_APP = 'digitalcrown-patient-companion';

export interface PatientAuthSnapshot {
  uid: string;
  email: string | null;
  emailVerified: boolean;
}

class PatientFirebaseUnavailable extends Error {
  constructor() {
    super('Authentification patient indisponible.');
    this.name = 'PatientFirebaseUnavailable';
  }
}

const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env ?? {};
const firebaseConfig = {
  apiKey: env.VITE_PATIENT_FIREBASE_API_KEY,
  authDomain: env.VITE_PATIENT_FIREBASE_AUTH_DOMAIN,
  projectId: env.VITE_PATIENT_FIREBASE_PROJECT_ID,
  appId: env.VITE_PATIENT_FIREBASE_APP_ID,
};

export function isPatientFirebaseConfigured(): boolean {
  return Boolean(
    firebaseConfig.apiKey
    && firebaseConfig.authDomain
    && firebaseConfig.projectId
    && firebaseConfig.appId,
  );
}

let authPromise: Promise<Auth> | null = null;

function patientApp(): FirebaseApp {
  if (!isPatientFirebaseConfigured()) throw new PatientFirebaseUnavailable();
  const existing = getApps().find((app) => app.name === PATIENT_FIREBASE_APP);
  return existing ?? initializeApp(firebaseConfig, PATIENT_FIREBASE_APP);
}

async function patientAuth(): Promise<Auth> {
  if (!authPromise) {
    authPromise = (async () => {
      const auth = getAuth(patientApp());
      try {
        await setPersistence(auth, browserSessionPersistence);
      } catch {
        // Shared/public devices must never be forced into durable local persistence.
        // If session storage is unavailable, memory-only auth remains safe and explicit.
        await setPersistence(auth, inMemoryPersistence);
      }
      return auth;
    })();
  }
  return authPromise;
}

function snapshot(user: User | null): PatientAuthSnapshot | null {
  if (!user) return null;
  return {
    uid: user.uid,
    email: user.email,
    emailVerified: user.emailVerified,
  };
}

export async function observePatientAuth(
  listener: (value: PatientAuthSnapshot | null) => void,
): Promise<() => void> {
  const auth = await patientAuth();
  return onAuthStateChanged(auth, (user) => listener(snapshot(user)));
}

export async function signInPatientWithEmail(email: string, password: string): Promise<PatientAuthSnapshot> {
  const auth = await patientAuth();
  const credential = await signInWithEmailAndPassword(auth, email.trim(), password);
  return snapshot(credential.user)!;
}

export async function createPatientWithEmail(email: string, password: string): Promise<PatientAuthSnapshot> {
  const auth = await patientAuth();
  const credential = await createUserWithEmailAndPassword(auth, email.trim(), password);
  await sendEmailVerification(credential.user);
  return snapshot(credential.user)!;
}

export async function resendPatientEmailVerification(): Promise<void> {
  const auth = await patientAuth();
  if (!auth.currentUser) throw new Error('Session patient absente.');
  await reload(auth.currentUser);
  if (!auth.currentUser.emailVerified) await sendEmailVerification(auth.currentUser);
}

export async function refreshPatientAuthSnapshot(): Promise<PatientAuthSnapshot | null> {
  const auth = await patientAuth();
  if (!auth.currentUser) return null;
  await reload(auth.currentUser);
  return snapshot(auth.currentUser);
}

export async function getVerifiedPatientIdToken(): Promise<string> {
  const auth = await patientAuth();
  const user = auth.currentUser;
  if (!user) throw new Error('Authentification patient requise.');
  await reload(user);
  if (!user.emailVerified) throw new Error('Adresse e-mail Firebase non vérifiée.');
  // Force a fresh token so the backend sees the current email_verified claim immediately.
  return user.getIdToken(true);
}

export async function signOutPatient(): Promise<void> {
  const auth = await patientAuth();
  await signOut(auth);
}

export function patientAuthErrorMessage(error: unknown): string {
  const code = typeof error === 'object' && error && 'code' in error
    ? String((error as { code?: unknown }).code ?? '')
    : '';
  if (code === 'auth/invalid-credential' || code === 'auth/wrong-password' || code === 'auth/user-not-found') {
    return 'E-mail ou mot de passe incorrect.';
  }
  if (code === 'auth/email-already-in-use') return 'Ce compte existe déjà. Connectez-vous.';
  if (code === 'auth/invalid-email') return 'Adresse e-mail invalide.';
  if (code === 'auth/weak-password') return 'Mot de passe insuffisamment robuste.';
  if (code === 'auth/too-many-requests') return 'Trop de tentatives. Réessayez plus tard.';
  if (error instanceof PatientFirebaseUnavailable) return error.message;
  return 'Authentification patient impossible pour le moment.';
}

export const patientAuthService = {
  configured: isPatientFirebaseConfigured,
  observe: observePatientAuth,
  signIn: signInPatientWithEmail,
  create: createPatientWithEmail,
  resendVerification: resendPatientEmailVerification,
  refresh: refreshPatientAuthSnapshot,
  getIdToken: getVerifiedPatientIdToken,
  signOut: signOutPatient,
};
