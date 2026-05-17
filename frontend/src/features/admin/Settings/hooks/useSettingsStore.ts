import { create } from 'zustand';
import { api } from '../../../../services/api';
import { safeStorage } from '../../../../hooks/useLocalStorage';
import type { CabinetProfile, ContactsJson } from '../types';
import toast from 'react-hot-toast';

interface SettingsState {
  profile: CabinetProfile;
  contacts: ContactsJson;
  loading: boolean;
  saving: boolean;
  saveSuccess: boolean;
  
  // Actions
  fetchProfile: () => Promise<void>;
  saveProfile: () => Promise<void>;
  updateProfile: (updates: Partial<CabinetProfile>) => void;
  updateContacts: (updates: Partial<ContactsJson>) => void;
  toggleContact: (type: string) => void;
  updateContactValue: (type: string, value: string) => void;
  
  // Media Actions
  uploadLogo: (file: File) => Promise<void>;
  uploadLetterhead: (file: File) => Promise<void>;
  deleteLogo: () => Promise<void>;
  applyTheme: () => void;
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
    qr_code_enabled: false,
    qr_code_type: 'VCARD',
    qr_code_value: '',
    qr_code_color: '',
    qr_code_label: '',
    show_patient_badges: true,
    nom_praticien_ar: '',
    specialty_ids: [],
    logo_path: '',
    font_fr: 'inter',
    selected_template: 'classic',
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

  fetchProfile: async () => {
    set({ loading: true });
    try {
      const res = await api.get('/clinics/me');
      if (res.data) {
        const profile = {
          nom: res.data.header_lines_fr?.[0] || res.data.nom_praticien || '',
          adresse: res.data.footer_address || res.data.adresse || '',
          telephone: res.data.footer_phones || res.data.telephone || '',
          inpe: res.data.inpe || '',
          ice: res.data.ice || '',
          if: res.data.if_ || res.data.if || '',
          margin_top: res.data.margin_top ?? 3.6,
          margin_bottom: res.data.margin_bottom ?? 3.2,
          watermark_enabled: res.data.watermark_enabled ?? true,
          letterhead_path: res.data.letterhead_path || undefined,
          selected_theme: res.data.selected_theme || 'elite',
          app_accent_color: res.data.app_accent_color || undefined,
          font_fr: res.data.font_fr || 'inter',
          selected_template: res.data.selected_template || 'classic',
          primary_color: res.data.primary_color || '#003380',
          secondary_color: res.data.secondary_color || '#1e40af',
          accent_color: res.data.accent_color || '#60a5fa',
          qr_code_enabled: res.data.qr_code_enabled ?? false,
          qr_code_type: res.data.qr_code_type || 'VCARD',
          qr_code_value: res.data.qr_code_value || '',
          qr_code_color: res.data.qr_code_color || '',
          qr_code_label: res.data.qr_code_label || '',
          show_patient_badges: res.data.show_patient_badges ?? true,
          nom_praticien_ar: res.data.nom_praticien_ar || '',
          specialty_ids: res.data.specialty_ids || [],
          logo_path: res.data.logo_path || '',
          header_lines_fr: res.data.header_lines_fr || [],
          header_lines_ar: res.data.header_lines_ar || [],
          header_scale: res.data.header_scale ?? 1.1,
          qr_code_style: res.data.qr_code_style || 'dots',
          header_font_scale: res.data.header_font_scale ?? 1.0,
          header_logo_scale: res.data.header_logo_scale ?? 1.0,
          header_line_height: res.data.header_line_height ?? 1.0,
          footer_font_scale: res.data.footer_font_scale ?? 1.0,
          footer_qr_scale: res.data.footer_qr_scale ?? 1.0,
          footer_line_height: res.data.footer_line_height ?? 1.0
        };
        
        set({ profile });
        localStorage.setItem('show_patient_badges', String(res.data.show_patient_badges ?? true));

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
      console.warn("Error fetching profile, using fallback", err);
    } finally {
      set({ loading: false });
      get().applyTheme();
    }
  },

  applyTheme: () => {
    const { profile } = get();
    const theme = profile.selected_theme || 'elite';
    
    // Application aux deux niveaux pour compatibilité maximale
    document.body.dataset.theme = theme === 'elite' ? '' : theme;
    document.documentElement.dataset.theme = theme === 'elite' ? '' : theme;
    
    // Sauvegarde localStorage pour le flash au chargement (App.tsx)
    localStorage.setItem('digitalcrown_theme', theme);
    
    // Application des couleurs accentuées
    if (profile.primary_color) {
      document.documentElement.style.setProperty('--primary', profile.primary_color);
      document.body.style.setProperty('--primary', profile.primary_color);
    }
    if (profile.secondary_color) {
      document.documentElement.style.setProperty('--secondary', profile.secondary_color);
    }
    if (profile.accent_color) {
      document.documentElement.style.setProperty('--accent', profile.accent_color);
    }
    
    // Support legacy pour la couleur d'accent d'application
    if (profile.app_accent_color) {
      document.documentElement.style.setProperty('--app-accent', profile.app_accent_color);
    }
  },

  updateProfile: (updates) => {
    set((state) => ({ profile: { ...state.profile, ...updates } }));
    if (updates.selected_theme || updates.primary_color || updates.accent_color) {
      get().applyTheme();
    }
  },
  
  updateContacts: (updates) => set((state) => ({ 
    contacts: { ...state.contacts, ...updates } as ContactsJson 
  })),

  toggleContact: (type) => set((state) => ({
    contacts: {
      ...state.contacts,
      [type]: { ...state.contacts[type], enabled: !state.contacts[type].enabled }
    }
  })),

  updateContactValue: (type, value) => set((state) => ({
    contacts: {
      ...state.contacts,
      [type]: { ...state.contacts[type], value }
    }
  })),

  saveProfile: async () => {
    set({ saving: true, saveSuccess: false });
    const { profile, contacts } = get();

    // Format phone string for backend legacy support
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
      const payload = {
        ...profile,
        footer_phones: contactString,
        contacts_json: contacts
      };

      await api.put('/clinics/me', payload);
      
      if (safeStorage.get('appMode') === 'demo') {
        sessionStorage.setItem('demoConfig', JSON.stringify({
          selected_theme: profile.selected_theme,
          primary_color: profile.primary_color,
          secondary_color: profile.secondary_color,
          accent_color: profile.accent_color
        }));
      }

      set({ saveSuccess: true });
      toast.success("Profil mis à jour");
      setTimeout(() => set({ saveSuccess: false }), 3000);
    } catch (err) {
      console.error("Save error", err);
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      set({ saving: false });
    }
  },

  uploadLogo: async (file: File) => {
    set({ saving: true });
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await api.post('/clinics/me/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      set((state) => ({ profile: { ...state.profile, logo_path: res.data.logo_url } }));
      toast.success("Logo mis à jour");
    } catch (err) {
      toast.error("Erreur upload logo");
    } finally {
      set({ saving: false });
    }
  },

  uploadLetterhead: async (file: File) => {
    set({ saving: true });
    const formData = new FormData();
    formData.append('file', file);
    const { profile } = get();
    formData.append('margins_top', (profile.margin_top || 3.6).toString());
    formData.append('margins_bottom', (profile.margin_bottom || 3.2).toString());
    try {
      const res = await api.post('/clinics/me/letterhead', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      set((state) => ({ 
        profile: { 
          ...state.profile, 
          letterhead_path: res.data.letterhead_url,
          watermark_enabled: false 
        } 
      }));
      toast.success("Papier en-tête mis à jour");
    } catch (err) {
      toast.error("Erreur upload en-tête");
    } finally {
      set({ saving: false });
    }
  },

  deleteLogo: async () => {
    try {
      await api.put('/clinics/me', { logo_path: null });
      set((state) => ({ profile: { ...state.profile, logo_path: '' } }));
      toast.success("Logo supprimé");
    } catch (err) {
      toast.error("Erreur suppression logo");
    }
  }
}));
