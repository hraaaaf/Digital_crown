import { create } from 'zustand';
import { api } from '../../../../services/api';
import { safeStorage } from '../../../../hooks/useLocalStorage';
import type { CabinetProfile, ContactsJson } from '../types';
import toast from 'react-hot-toast';

const syncRuntimePreferences = (profile: Pick<CabinetProfile, 'show_patient_badges' | 'performance_mode' | 'clinical_tips_enabled'>) => {
  safeStorage.set('show_patient_badges', String(profile.show_patient_badges ?? true));
  safeStorage.set('performanceMode', String(profile.performance_mode ?? false));
  safeStorage.set('clinical_tips_enabled', String(profile.clinical_tips_enabled ?? true));
  safeStorage.set('clinicalTipsEnabled', String(profile.clinical_tips_enabled ?? true));
  window.dispatchEvent(new Event('settings_updated'));
  window.dispatchEvent(new Event('clinical-tips-changed'));
};

interface SettingsState {
  profile: CabinetProfile;
  contacts: ContactsJson;
  loading: boolean;
  saving: boolean;
  saveSuccess: boolean;
  isDirty: boolean;

  fetchProfile: () => Promise<void>;
  saveProfile: () => Promise<void>;
  updateProfile: (updates: Partial<CabinetProfile>) => void;
  updateContacts: (updates: Partial<ContactsJson>) => void;
  toggleContact: (type: string) => void;
  updateContactValue: (type: string, value: string) => void;

  uploadLogo: (file: File) => Promise<void>;
  uploadLetterhead: (file: File, options?: { stripBody?: boolean; headerPct?: number; footerPct?: number }) => Promise<void>;
  deleteLetterhead: () => Promise<void>;
  deleteLogo: () => Promise<void>;
  applyTheme: (options?: { persist?: boolean }) => void;
  activeCabinetId: string;
  cabinets: Array<{ id: string; nom: string; specialty: string; primary_color: string; accent_color: string; theme: string; caisse: number }>;
  switchCabinet: (id: string) => void;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  profile: {
    nom: '',
    adresse: '',
    telephone: '',
    inpe: '',
    margin_top: 3.6,
    margin_bottom: 3.2,
    watermark_enabled: true,
    use_letterhead: false,
    qr_code_enabled: false,
    qr_code_type: 'VCARD',
    qr_code_value: '',
    qr_code_color: '',
    qr_code_label: '',
    show_patient_badges: true,
    performance_mode: false,
    clinical_tips_enabled: true,
    hide_header: true,
    hide_footer: true,
    cabinet_type: 'PRIVE',
    nom_praticien_ar: '',
    specialty_ids: [],
    custom_specialty_fr: '',
    custom_specialty_ar: '',
    logo_path: '',
    font_fr: 'inter',
    selected_template: 'swiss',
    header_lines_fr: [],
    header_lines_ar: [],
    qr_code_style: 'dots',
    header_font_scale: 1.0,
    header_logo_scale: 1.0,
    header_line_height: 1.0,
    footer_font_scale: 1.0,
    footer_qr_scale: 1.0,
    footer_line_height: 1.0
  },
  contacts: {
    fixe: { enabled: true, value: '' },
    mobile: { enabled: false, value: '' },
    whatsapp: { enabled: false, value: '' },
    instagram: { enabled: false, value: '' }
  },
  loading: true,
  saving: false,
  saveSuccess: false,
  isDirty: false,

  fetchProfile: async () => {
    set({ loading: true });
    let profileLoaded = false;
    try {
      const res = await api.get('/clinics/me');
      if (res.data) {
        const activeId = localStorage.getItem('active_cabinet_id') || 'default';

        const dynamicCabinet = {
          id: activeId,
          nom: res.data.nom_cabinet || res.data.nom_praticien || 'Mon Cabinet',
          specialty: res.data.header_lines_fr?.[1] || 'Chirurgien Dentiste',
          primary_color: res.data.primary_color || '#1E40AF',
          accent_color: res.data.accent_color || '#3B82F6',
          theme: res.data.selected_theme || 'elite',
          caisse: 0
        };
        set({ cabinets: [dynamicCabinet] });
        const cabinet = dynamicCabinet;

        const profile = {
          nom: res.data.nom_praticien || (cabinet ? cabinet.nom : ''),
          adresse: res.data.footer_address || res.data.adresse || '',
          telephone: res.data.footer_phones || res.data.telephone || '',
          inpe: res.data.inpe || '',
          ice: res.data.ice || '',
          if: res.data.if_ || res.data.if || '',
          margin_top: res.data.margin_top ?? 3.6,
          margin_bottom: res.data.margin_bottom ?? 3.2,
          watermark_enabled: res.data.watermark_enabled ?? true,
          letterhead_path: res.data.letterhead_path || undefined,
          use_letterhead: res.data.use_letterhead ?? false,
          selected_theme: res.data.selected_theme || (cabinet ? cabinet.theme : 'elite'),
          app_accent_color: res.data.app_accent_color || undefined,
          font_fr: res.data.font_fr || 'inter',
          selected_template: res.data.selected_template || 'swiss',
          primary_color: res.data.primary_color || (cabinet ? cabinet.primary_color : '#003380'),
          secondary_color: res.data.secondary_color || '#1e40af',
          accent_color: res.data.accent_color || (cabinet ? cabinet.accent_color : '#60a5fa'),
          qr_code_enabled: res.data.qr_code_enabled ?? false,
          qr_code_type: res.data.qr_code_type || 'VCARD',
          qr_code_value: res.data.qr_code_value || '',
          qr_code_color: res.data.qr_code_color || '',
          qr_code_label: res.data.qr_code_label || '',
          show_patient_badges: res.data.show_patient_badges ?? true,
          performance_mode: res.data.performance_mode ?? false,
          clinical_tips_enabled: res.data.clinical_tips_enabled ?? true,
          hide_header: res.data.hide_header ?? true,
          hide_footer: res.data.hide_footer ?? true,
          cabinet_type: res.data.cabinet_type || 'PRIVE',
          nom_praticien_ar: res.data.nom_praticien_ar || '',
          specialty_ids: res.data.specialty_ids || [],
          custom_specialty_fr: res.data.custom_specialty_fr || '',
          custom_specialty_ar: res.data.custom_specialty_ar || '',
          logo_path: res.data.logo_path || '',
          header_lines_fr: (() => {
            const drPrefixes = ['Dr.', 'Dr ', 'Pr.', 'Pr ', 'Docteur', 'Professeur'];
            const raw: string[] = res.data.header_lines_fr?.length
              ? res.data.header_lines_fr
              : cabinet ? [cabinet.nom, cabinet.specialty] : [];
            if (raw.length > 0 && !drPrefixes.some(p => raw[0].startsWith(p))) {
              return [raw[0] ? `Dr. ${raw[0]}` : raw[0], ...raw.slice(1)];
            }
            return raw;
          })(),
          header_lines_ar: res.data.header_lines_ar || [],
          header_scale: res.data.header_scale ?? 1.1,
          qr_code_style: res.data.qr_code_style || 'dots',
          header_font_scale: res.data.header_font_scale ?? 1.0,
          header_logo_scale: res.data.header_logo_scale ?? 1.0,
          header_line_height: res.data.header_line_height ?? 1.0,
          footer_font_scale: res.data.footer_font_scale ?? 1.0,
          footer_qr_scale: res.data.footer_qr_scale ?? 1.0,
          footer_line_height: res.data.footer_line_height ?? 1.0,
          nom_cabinet: res.data.nom_cabinet || ''
        };

        set({ profile });
        syncRuntimePreferences(profile);
        profileLoaded = true;

        if (res.data.contacts_json && Object.keys(res.data.contacts_json).length > 0) {
          set({ contacts: res.data.contacts_json as ContactsJson });
        } else if (res.data.footer_phones) {
          set({ contacts: {
            ...get().contacts,
            fixe: { enabled: true, value: res.data.footer_phones }
          } as ContactsJson });
        }
      }
    } catch (err) {
      console.warn('Error fetching profile, using fallback', err);
    } finally {
      set({ loading: false, isDirty: false });
      get().applyTheme({ persist: profileLoaded });
    }
  },

  applyTheme: (options = { persist: true }) => {
    const { profile } = get();
    const finalTheme = profile.selected_theme || 'elite';

    document.body.dataset.theme = finalTheme === 'elite' ? '' : finalTheme;
    document.documentElement.dataset.theme = finalTheme === 'elite' ? '' : finalTheme;
    if (options.persist !== false) {
      localStorage.setItem('digitalcrown_theme', finalTheme);
    }

    if (profile.primary_color) {
      document.documentElement.style.setProperty('--primary', profile.primary_color);
      document.body.style.setProperty('--primary', profile.primary_color);

      const hex = profile.primary_color.replace('#', '');
      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);
      const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
      const textOnPrimary = (yiq >= 128) ? '#0f172a' : '#ffffff';
      document.documentElement.style.setProperty('--text-on-primary', textOnPrimary);
      document.body.style.setProperty('--text-on-primary', textOnPrimary);
    } else {
      document.documentElement.style.removeProperty('--primary');
      document.body.style.removeProperty('--primary');
      document.documentElement.style.removeProperty('--text-on-primary');
      document.body.style.removeProperty('--text-on-primary');
    }

    if (profile.secondary_color) {
      document.documentElement.style.setProperty('--secondary', profile.secondary_color);
    } else {
      document.documentElement.style.removeProperty('--secondary');
    }

    if (profile.accent_color) {
      document.documentElement.style.setProperty('--accent', profile.accent_color);
    } else {
      document.documentElement.style.removeProperty('--accent');
    }

    if (profile.app_accent_color) {
      document.documentElement.style.setProperty('--app-accent', profile.app_accent_color);
    }

    let metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta');
      metaThemeColor.setAttribute('name', 'theme-color');
      document.head.appendChild(metaThemeColor);
    }
    const isDark = ['prestige', 'graphite'].includes(finalTheme);
    metaThemeColor.setAttribute('content', isDark ? '#020617' : '#f8fafc');
  },

  updateProfile: (updates) => {
    set((state) => ({
      profile: { ...state.profile, ...updates },
      isDirty: true,
    }));
    if (updates.selected_theme || updates.primary_color || updates.accent_color) {
      get().applyTheme({ persist: false });
    }
  },

  updateContacts: (updates) => set((state) => ({
    contacts: { ...state.contacts, ...updates } as ContactsJson,
    isDirty: true
  })),

  toggleContact: (type) => set((state) => ({
    contacts: {
      ...state.contacts,
      [type]: { ...state.contacts[type], enabled: !state.contacts[type].enabled }
    },
    isDirty: true
  })),

  updateContactValue: (type, value) => set((state) => ({
    contacts: {
      ...state.contacts,
      [type]: { ...state.contacts[type], value }
    },
    isDirty: true
  })),

  saveProfile: async () => {
    set({ saving: true, saveSuccess: false });
    const { profile, contacts } = get();

    const parts: string[] = [];
    Object.keys(contacts).forEach(type => {
      const c = contacts[type];
      if (c.enabled && c.value.trim()) {
        const icon = type === 'fixe' ? '📞' : type === 'mobile' ? '📱' : type === 'whatsapp' ? '💬' : '📸';
        parts.push(`${icon} ${c.value.trim()}`);
      }
    });
    const contactString = parts.join(' | ');

    try {
      const { logo_path: _logoPath, ...persistableProfile } = profile;
      const payload = {
        ...persistableProfile,
        footer_phones: contactString,
        contacts_json: contacts
      };

      await api.put('/clinics/me', payload);
      get().applyTheme({ persist: true });
      syncRuntimePreferences(profile);

      if (safeStorage.get('appMode') === 'demo') {
        sessionStorage.setItem('demoConfig', JSON.stringify({
          selected_theme: profile.selected_theme,
          primary_color: profile.primary_color,
          secondary_color: profile.secondary_color,
          accent_color: profile.accent_color
        }));
      }

      set({ saveSuccess: true, isDirty: false });
      toast.success('Configuration enregistrée');
      setTimeout(() => set({ saveSuccess: false }), 3000);
    } catch (err) {
      console.error('Save error', err);
      toast.error('Erreur lors de la sauvegarde');
      throw err;
    } finally {
      set({ saving: false });
    }
  },

  uploadLogo: async (file: File) => {
    set({ saving: true });
    const formData = new FormData();
    formData.append('file', file);

    const uploadPromise = api.post('/clinics/me/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    toast.promise(uploadPromise, {
      loading: 'Optimisation du logo en cours...',
      success: 'Logo optimisé et enregistré',
      error: 'Erreur lors du traitement du logo'
    });

    try {
      const res = await uploadPromise;
      set((state) => ({ profile: { ...state.profile, logo_path: res.data.logo_url } }));
    } catch (err) {
      // toast already handled
    } finally {
      set({ saving: false });
    }
  },

  uploadLetterhead: async (file: File, options?: { stripBody?: boolean; headerPct?: number; footerPct?: number }) => {
    set({ saving: true });
    const formData = new FormData();
    formData.append('file', file);
    const { profile } = get();
    formData.append('margins_top', (profile.margin_top || 3.6).toString());
    formData.append('margins_bottom', (profile.margin_bottom || 3.2).toString());
    formData.append('hide_header', String(profile.hide_header ?? true));
    formData.append('hide_footer', String(profile.hide_footer ?? true));
    formData.append('strip_body', String(options?.stripBody ?? false));
    formData.append('header_pct', String(options?.headerPct ?? 25));
    formData.append('footer_pct', String(options?.footerPct ?? 18));
    try {
      const res = await api.post('/clinics/me/letterhead', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const normalizedLetterheadPath = typeof res.data.letterhead_url === 'string'
        ? res.data.letterhead_url.replace(/^\/?static\/uploads\//, '')
        : res.data.letterhead_url;
      set((state) => ({
        profile: {
          ...state.profile,
          letterhead_path: normalizedLetterheadPath,
          use_letterhead: res.data.use_letterhead ?? true,
          hide_header: res.data.hide_default_header ?? true,
          hide_footer: res.data.hide_default_footer ?? true,
          watermark_enabled: false,
          primary_color: res.data.detected_colors?.primary_color || state.profile.primary_color,
          secondary_color: res.data.detected_colors?.secondary_color || state.profile.secondary_color,
          accent_color: res.data.detected_colors?.accent_color || state.profile.accent_color
        }
      }));
      toast.success('Papier en-tête mis à jour');
    } catch (err) {
      toast.error('Erreur upload en-tête');
    } finally {
      set({ saving: false });
    }
  },

  deleteLetterhead: async () => {
    try {
      await api.put('/clinics/me', { letterhead_path: null, use_letterhead: false });
      set((state) => ({ profile: { ...state.profile, letterhead_path: '', use_letterhead: false } }));
      toast.success('Fond de page supprimé');
    } catch (err) {
      toast.error('Erreur suppression du fond de page');
    }
  },

  deleteLogo: async () => {
    try {
      await api.put('/clinics/me', { logo_path: null });
      set((state) => ({ profile: { ...state.profile, logo_path: '' } }));
      toast.success('Logo supprimé');
    } catch (err) {
      toast.error('Erreur suppression logo');
    }
  },

  activeCabinetId: localStorage.getItem('active_cabinet_id') || 'default',
  cabinets: [],
  switchCabinet: (id: string) => {
    const cabinet = get().cabinets.find(c => c.id === id);
    if (!cabinet) return;

    set({ activeCabinetId: id });
    localStorage.setItem('active_cabinet_id', id);

    const updatedProfile = {
      ...get().profile,
      nom: cabinet.nom,
      primary_color: cabinet.primary_color,
      accent_color: cabinet.accent_color,
      selected_theme: cabinet.theme,
      header_lines_fr: [cabinet.nom, cabinet.specialty]
    };

    set({ profile: updatedProfile });
    get().applyTheme();

    window.dispatchEvent(new CustomEvent('cabinet-changed', { detail: { cabinet } }));
    toast.success(`Transition réussie vers ${cabinet.nom}`);
  }
}));
