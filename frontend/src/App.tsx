import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { lazy, Suspense, useEffect, useState } from 'react';
import axios from 'axios';
import { MainLayout } from './components/Layout/MainLayout';
import { cabinetApi } from './services/templateApi';
import { API_BASE } from './services/api';
import { safeStorage } from './hooks/useLocalStorage';
import { useAuthStore } from './stores/useAuthStore';

// Chargés immédiatement (première interaction utilisateur)
import { Dashboard } from './pages/Dashboard';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { WelcomeScreen } from './pages/WelcomeScreen';
import { LandingPage } from './pages/LandingPage';
import { DownloadPage } from './pages/DownloadPage';
import { ActivateTrialPage } from './pages/ActivateTrialPage';
import { authService } from './services/auth';

// Chargés à la demande
const PatientList     = lazy(() => import('./features/patients/PatientList').then(m => ({ default: m.PatientList })));
const PatientDetails  = lazy(() => import('./features/patients/PatientDetails').then(m => ({ default: m.PatientDetails })));
const AddPatientForm  = lazy(() => import('./features/patients/AddPatientForm').then(m => ({ default: m.AddPatientForm })));
const EditPatientForm = lazy(() => import('./features/patients/EditPatientForm').then(m => ({ default: m.EditPatientForm })));
const PatientDocuments = lazy(() => import('./features/patients/PatientDocuments').then(m => ({ default: m.PatientDocuments })));
const AgendaPage      = lazy(() => import('./pages/AgendaPage').then(m => ({ default: m.AgendaPage })));
const AccountingPage  = lazy(() => import('./pages/AccountingPage').then(m => ({ default: m.AccountingPage })));
const Settings        = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })));
const Analytics       = lazy(() => import('./pages/Analytics').then(m => ({ default: m.Analytics })));
const SetupWizard     = lazy(() => import('./features/admin/SetupWizard').then(m => ({ default: m.SetupWizard })));
const EliteLibrary    = lazy(() => import('./features/clinical-ref/EliteLibrary').then(m => ({ default: m.EliteLibrary })));
const EliteScienceHub = lazy(() => import('./features/clinical-ref/EliteScienceHub').then(m => ({ default: m.EliteScienceHub })));
const SuperAdminDashboard = lazy(() => import('./features/superadmin/SuperAdminDashboard').then(m => ({ default: m.SuperAdminDashboard })));
// Module Labo — EN CONSTRUCTION / BIENTÔT DISPONIBLE (désactivé temporairement)
// const LabJobsBoard    = lazy(() => import('./components/LabJobsBoard').then(m => ({ default: m.LabJobsBoard })));
const LegalPage       = lazy(() => import('./pages/LegalPage').then(m => ({ default: m.LegalPage })));

// MOBILE PWA
const OnboardingScanner = lazy(() => import('./features/mobile/Onboarding/OnboardingScanner').then(m => ({ default: m.OnboardingScanner })));
const MobileDashboard  = lazy(() => import('./features/mobile/Dashboard/MobileDashboard').then(m => ({ default: m.MobileDashboard })));
const DentistsView     = lazy(() => import('./features/mobile/Dashboard/views/DentistsView').then(m => ({ default: m.DentistsView })));

import { MobileStorage } from './services/zka/MobileStorage';

import { DigitalCrownLoader } from './components/DigitalCrownLoader';
import { ComingSoon } from './components/ComingSoon';

const PageLoader = () => (
  <DigitalCrownLoader minHeight="min-h-[60vh]" className="bg-transparent" spinnerColor="border-blue-600" />
);

// ==============================================================================
// COMPOSANT DE PROTECTION DES ROUTES
// ==============================================================================

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState<boolean | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const location = useLocation();

  useEffect(() => {
    const checkAuthAndInit = async () => {
      // 1. Attendre que la base de données / le backend soit complètement chargé
      const waitForBackend = async () => {
        const MAX_ATTEMPTS = 15; // 15 × 2s = 30s max
        for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
          try {
            await axios.get(`${API_BASE}/health`);
            break;
          } catch (error: any) {
            if (error.response && error.response.status !== 502 && error.response.status !== 503) {
              break;
            }
            if (attempt < MAX_ATTEMPTS - 1) {
              await new Promise(resolve => setTimeout(resolve, 2000));
            }
          }
        }
      };

      try {
        await waitForBackend();
        
        const authStatus = await authService.isAuthenticated();
        setIsAuthenticated(authStatus);
        
        if (authStatus && location.pathname !== '/login') {
          await useAuthStore.getState().checkAuth();
          const status = await cabinetApi.checkInitStatus();
          setIsInitialized(status.is_initialized);
          
          if (status.is_initialized && !safeStorage.get('appMode')) {
            safeStorage.set('appMode', 'prod');
          }
        }
      } catch (error) {
        console.error('Erreur vérification statut:', error);
        setIsInitialized(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthAndInit();
  }, [location.pathname]);

  if (isLoading) {
    return <DigitalCrownLoader text="Patientez pendant le démarrage de l'IA..." />;
  }

  // BYPASS AUTH : Si on est sur /login et pas connecté, on laisse passer pour afficher la page
  if (!isAuthenticated) {
    if (['/login', '/register', '/terms', '/privacy'].includes(location.pathname)) return <>{children}</>;
    return <Navigate to="/login" replace />;
  }

  // Force le choix du mode s'il n'existe pas (Mode PROD par défaut désormais)
  const appMode = safeStorage.get('appMode');
  if (!appMode) {
    safeStorage.set('appMode', 'prod');
  }

  // Si le cabinet est déjà initialisé, on empêche l'accès au setup
  if (isInitialized && location.pathname === '/setup') {
    return <Navigate to="/dashboard" replace />;
  }

  // Nouveau cabinet non configuré → forcer le wizard (sauf si déjà sur /setup)
  if (isInitialized === false && location.pathname !== '/setup') {
    return <Navigate to="/setup" replace />;
  }

  return <>{children}</>;
};

// ==============================================================================
// PROTECTION PWA MOBILE (ZKA)
// ==============================================================================

const MobileProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const [isPaired, setIsPaired] = useState<boolean | null>(null);

  useEffect(() => {
    MobileStorage.isPaired().then(setIsPaired);
  }, []);

  if (isPaired === null) return <PageLoader />;
  if (!isPaired) return <Navigate to="/mobile/onboarding" replace />;

  return <>{children}</>;
};



// =============================================================================
// ROUTES PROTÉGÉES (avec layout)
// =============================================================================

const ProtectedRoutes = () => (
  <MainLayout>
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/agenda" element={<AgendaPage />} />
        <Route path="/accounting" element={<AccountingPage />} />
        <Route path="/patients" element={<PatientList />} />
        <Route path="/patients/new" element={<AddPatientForm />} />
        <Route path="/patients/:id" element={<PatientDetails />} />
        <Route path="/patients/:id/archives" element={<PatientDocuments />} />
        <Route path="/patients/:id/edit" element={<EditPatientForm />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/analytics" element={<Analytics />} />
        {/* Module Labo — EN CONSTRUCTION / BIENTÔT DISPONIBLE */}
        <Route path="/labo" element={<ComingSoon title="Module Labo" description="Le suivi des travaux de laboratoire (prothèses) sera bientôt disponible." />} />
        {/* <Route path="/labo" element={<LabJobsBoard />} /> */}
        <Route path="/bibliotheque" element={<EliteLibrary />} />
        <Route path="/bibliotheque/:code" element={<EliteLibrary />} />
        <Route path="/science-hub" element={<EliteScienceHub />} />
        <Route path="/super-admin" element={<SuperAdminDashboard />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  </MainLayout>
);

// =============================================================================
// ROUTAGE INTELLIGENT PWA (Mobile vs Desktop)
// =============================================================================

const SmartRootRouter = () => {
  const isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone/i.test(navigator.userAgent);
  const [authStatus, setAuthStatus] = useState<'checking' | 'authenticated' | 'anonymous'>('checking');

  useEffect(() => {
    if (isMobile) return;

    let cancelled = false;

    const resolveAuth = async () => {
      try {
        const isAuthenticated = await authService.isAuthenticated();
        if (!cancelled) {
          setAuthStatus(isAuthenticated ? 'authenticated' : 'anonymous');
        }
      } catch {
        if (!cancelled) {
          setAuthStatus('anonymous');
        }
      }
    };

    resolveAuth();

    return () => {
      cancelled = true;
    };
  }, [isMobile]);
  if (isMobile) {
    return <Navigate to="/mobile/dashboard" replace />;
  }
  // Connecté → dashboard directement ; non-connecté → page marketing publique
  if (authStatus === 'checking') {
    return <PageLoader />;
  }
  if (authStatus === 'authenticated') {
    return <Navigate to="/dashboard" replace />;
  }
  return <Navigate to="/landing" replace />;
};

// =============================================================================
// APP PRINCIPAL
// =============================================================================

import { OfflineQueueViewer } from './components/mobile/OfflineQueueViewer';

function App() {
  const [animatedBg, setAnimatedBg] = useState(() => safeStorage.get('app_background_animated') === 'true');

  // Application globale du thème (Persistance) et Paramètres IA
  useEffect(() => {
    const savedTheme = localStorage.getItem('digitalcrown_theme');
    if (savedTheme) {
      document.body.dataset.theme = savedTheme;
    }

    const applySettings = () => {
      // Mode Performance
      const isPerfMode = safeStorage.get('performanceMode') === 'true';
      if (isPerfMode) {
        document.body.classList.add('performance-mode');
      } else {
        document.body.classList.remove('performance-mode');
      }

      // Arrière-plan Animé
      setAnimatedBg(safeStorage.get('app_background_animated') === 'true');
    };

    applySettings();

    // Permet la mise à jour réactive sans recharger si déclenché manuellement
    window.addEventListener('settings_updated', applySettings);
    return () => window.removeEventListener('settings_updated', applySettings);
  }, []);

  return (
    <BrowserRouter>
      <OfflineQueueViewer />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: { borderRadius: '16px', fontWeight: 700, fontSize: '13px' },
          success: { duration: 3000 },
          error: { duration: 5000 },
        }}
      />
      <Routes>
        {/* ROUTAGE INTELLIGENT RACINE (PWA Entry Point) */}
        <Route path="/" element={<SmartRootRouter />} />

        {/* ROUTES PWA MOBILE (Accès Direct) */}
        <Route path="/mobile/onboarding" element={
          <Suspense fallback={<PageLoader />}><OnboardingScanner /></Suspense>
        } />
        <Route path="/mobile/dashboard" element={
          <MobileProtectedRoute>
            <Suspense fallback={<PageLoader />}><MobileDashboard /></Suspense>
          </MobileProtectedRoute>
        } />
        <Route path="/mobile/dentists" element={
          <MobileProtectedRoute>
            <Suspense fallback={<PageLoader />}><DentistsView /></Suspense>
          </MobileProtectedRoute>
        } />
        
        {/* Page marketing publique (avant connexion) */}
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/download" element={<DownloadPage />} />
        <Route path="/activate" element={<ActivateTrialPage />} />
        <Route path="/welcome" element={<Navigate to="/landing" replace />} />

        {/* Toutes les autres routes passent par le filtre Mode/Init */}
        <Route path="/*" element={
          <ProtectedRoute>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/terms" element={<LegalPage type="terms" />} />
                <Route path="/privacy" element={<LegalPage type="privacy" />} />
                <Route path="/setup" element={<SetupWizard />} />
                <Route path="/*" element={<ProtectedRoutes />} />
              </Routes>
            </Suspense>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
