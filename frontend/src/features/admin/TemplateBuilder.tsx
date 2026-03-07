import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Palette, 
  Type, 
  Layout, 
  Eye, 
  Save, 
  Undo,
  FileText,
  Image as ImageIcon,
  Check
} from 'lucide-react';
import { cabinetApi, templateApi } from '../../services/templateApi';
import type { 
  DocumentTemplate, 
  DesignConfig, 
  CabinetConfig
} from '../../types/template';
import { cn } from '../../utils/cn';

// --- Composants utilitaires ---

interface ColorPickerProps {
  label: string;
  value: string;
  onChange: (color: string) => void;
}

const ColorPicker: React.FC<ColorPickerProps> = ({ label, value, onChange }) => (
  <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-200">
    <span className="text-sm font-medium text-slate-700">{label}</span>
    <div className="flex items-center gap-2">
      <input
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-8 h-8 rounded cursor-pointer border-0 p-0"
      />
      <span className="text-xs font-mono text-slate-500">{value}</span>
    </div>
  </div>
);

interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (val: number) => void;
  unit?: string;
}

const Slider: React.FC<SliderProps> = ({ label, value, min, max, step = 1, onChange, unit = '' }) => (
  <div className="space-y-2">
    <div className="flex justify-between">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <span className="text-sm text-slate-500">{value}{unit}</span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
    />
  </div>
);

// --- Composant Principal ---

export const TemplateBuilder: React.FC = () => {
  const { templateId } = useParams<{ templateId: string }>();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [template, setTemplate] = useState<DocumentTemplate | null>(null);
  const [cabinet, setCabinet] = useState<CabinetConfig | null>(null);
  const [activeTab, setActiveTab] = useState<'general' | 'typography' | 'layout' | 'watermark'>('general');
  
  // Design config local (modifications en cours)
  const [designConfig, setDesignConfig] = useState<DesignConfig | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    loadData();
  }, [templateId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [templateData, cabinetData] = await Promise.all([
        templateApi.getById(templateId!),
        cabinetApi.getMine(),
      ]);
      
      setTemplate(templateData);
      setCabinet(cabinetData);
      setDesignConfig(templateData.design_config);
    } catch (error) {
      console.error('Erreur chargement template:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDesignChange = (path: string, value: any) => {
    if (!designConfig) return;
    
    const newConfig = { ...designConfig };
    const keys = path.split('.');
    let current: any = newConfig;
    
    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;
    
    setDesignConfig(newConfig);
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!template || !designConfig) return;
    
    try {
      setSaving(true);
      await templateApi.update(template.id, {
        design_config: designConfig,
      });
      setHasChanges(false);
      alert('Modifications sauvegardées avec succès !');
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
      alert('Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const handlePreview = async () => {
    if (!template) return;
    
    try {
      const blob = await templateApi.preview({ template_id: template.id });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (error) {
      console.error('Erreur preview:', error);
      alert('Erreur lors de la génération du preview');
    }
  };

  const handleSetDefault = async () => {
    if (!template) return;
    
    try {
      await templateApi.setDefault(template.id);
      alert('Template défini comme défaut !');
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!template || !designConfig || !cabinet) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-slate-500">Template non trouvé</p>
      </div>
    );
  }

  // Si template système, afficher message lecture seule pour certaines parties
  const isSystemTemplate = template.is_system;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/settings/templates')}
                className="p-2 text-slate-400 hover:text-slate-600 transition-colors"
              >
                <Undo className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-slate-900">{template.name}</h1>
                <p className="text-sm text-slate-500">
                  {template.type} • Style {template.style_key}
                  {isSystemTemplate && (
                    <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                      Système
                    </span>
                  )}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {!template.is_default && (
                <button
                  onClick={handleSetDefault}
                  className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Définir par défaut
                </button>
              )}
              {template.is_default && (
                <span className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-green-700 bg-green-100 rounded-lg">
                  <Check className="w-4 h-4" />
                  Par défaut
                </span>
              )}
              
              <button
                onClick={handlePreview}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
              >
                <Eye className="w-4 h-4" />
                Aperçu
              </button>
              
              <button
                onClick={handleSave}
                disabled={!hasChanges || saving}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors",
                  hasChanges && !saving
                    ? "bg-blue-600 hover:bg-blue-700"
                    : "bg-slate-400 cursor-not-allowed"
                )}
              >
                <Save className="w-4 h-4" />
                {saving ? 'Sauvegarde...' : 'Sauvegarder'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1 space-y-6">
            {/* Tabs */}
            <nav className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              {[
                { id: 'general', label: 'Général', icon: Palette },
                { id: 'typography', label: 'Typographie', icon: Type },
                { id: 'layout', label: 'Mise en page', icon: Layout },
                { id: 'watermark', label: 'Filigrane', icon: ImageIcon },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 text-left transition-colors",
                    activeTab === tab.id
                      ? "bg-blue-50 text-blue-700 border-r-2 border-blue-600"
                      : "text-slate-600 hover:bg-slate-50"
                  )}
                >
                  <tab.icon className="w-5 h-5" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">
                <FileText className="w-4 h-4 inline mr-1" />
                Informations
              </h4>
              <p className="text-xs text-blue-700">
                Les modifications affecteront uniquement l'apparence visuelle. 
                La structure du document reste inchangée.
              </p>
              {isSystemTemplate && (
                <p className="text-xs text-orange-600 mt-2">
                  Template système : certaines options sont en lecture seule.
                </p>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Tab Content */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              
              {/* GENERAL */}
              {activeTab === 'general' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-semibold text-slate-900">Apparence générale</h2>
                  
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-slate-700">Couleurs</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <ColorPicker
                        label="Couleur principale"
                        value={designConfig.colors.primary}
                        onChange={(v) => handleDesignChange('colors.primary', v)}
                      />
                      <ColorPicker
                        label="Couleur secondaire"
                        value={designConfig.colors.secondary}
                        onChange={(v) => handleDesignChange('colors.secondary', v)}
                      />
                      <ColorPicker
                        label="Couleur d'accent"
                        value={designConfig.colors.accent}
                        onChange={(v) => handleDesignChange('colors.accent', v)}
                      />
                      <ColorPicker
                        label="Fond"
                        value={designConfig.colors.background}
                        onChange={(v) => handleDesignChange('colors.background', v)}
                      />
                    </div>
                  </div>

                  <div className="border-t border-slate-200 pt-6 space-y-4">
                    <h3 className="text-sm font-medium text-slate-700">Bordures</h3>
                    <div className="space-y-3">
                      <label className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={designConfig.borders.header_line}
                          onChange={(e) => handleDesignChange('borders.header_line', e.target.checked)}
                          className="w-4 h-4 text-blue-600 rounded border-slate-300"
                        />
                        <span className="text-sm text-slate-700">Ligne sous l'en-tête</span>
                      </label>
                      
                      {designConfig.borders.header_line && (
                        <ColorPicker
                          label="Couleur de la ligne"
                          value={designConfig.borders.header_line_color}
                          onChange={(v) => handleDesignChange('borders.header_line_color', v)}
                        />
                      )}
                      
                      <label className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={designConfig.borders.content_border}
                          onChange={(e) => handleDesignChange('borders.content_border', e.target.checked)}
                          className="w-4 h-4 text-blue-600 rounded border-slate-300"
                        />
                        <span className="text-sm text-slate-700">Bordure autour du contenu</span>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* TYPOGRAPHY */}
              {activeTab === 'typography' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-semibold text-slate-900">Typographie</h2>
                  
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <h3 className="text-sm font-medium text-slate-700">Titre principal</h3>
                      
                      <Slider
                        label="Taille de police"
                        value={designConfig.typography.title_size}
                        min={12}
                        max={32}
                        onChange={(v) => handleDesignChange('typography.title_size', v)}
                        unit="pt"
                      />
                      
                      <div className="flex gap-4">
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={designConfig.typography.title_bold}
                            onChange={(e) => handleDesignChange('typography.title_bold', e.target.checked)}
                            className="w-4 h-4 text-blue-600 rounded border-slate-300"
                          />
                          <span className="text-sm text-slate-700">Gras</span>
                        </label>
                        
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={designConfig.typography.title_underline}
                            onChange={(e) => handleDesignChange('typography.title_underline', e.target.checked)}
                            className="w-4 h-4 text-blue-600 rounded border-slate-300"
                          />
                          <span className="text-sm text-slate-700">Souligné</span>
                        </label>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium text-slate-700">Alignement</label>
                        <div className="mt-2 flex gap-2">
                          {['left', 'center', 'right'].map((align) => (
                            <button
                              key={align}
                              onClick={() => handleDesignChange('typography.title_align', align)}
                              className={cn(
                                "px-3 py-1.5 text-sm rounded-lg border transition-colors",
                                designConfig.typography.title_align === align
                                  ? "bg-blue-100 border-blue-300 text-blue-700"
                                  : "bg-white border-slate-300 text-slate-700 hover:bg-slate-50"
                              )}
                            >
                              {align === 'left' && 'Gauche'}
                              {align === 'center' && 'Centre'}
                              {align === 'right' && 'Droite'}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="border-t border-slate-200 pt-6 space-y-4">
                      <h3 className="text-sm font-medium text-slate-700">Corps du texte</h3>
                      
                      <Slider
                        label="Taille de police"
                        value={designConfig.typography.body_size}
                        min={8}
                        max={16}
                        onChange={(v) => handleDesignChange('typography.body_size', v)}
                        unit="pt"
                      />
                      
                      <Slider
                        label="Interligne"
                        value={designConfig.typography.body_line_height}
                        min={1}
                        max={2.5}
                        step={0.1}
                        onChange={(v) => handleDesignChange('typography.body_line_height', v)}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* LAYOUT */}
              {activeTab === 'layout' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-semibold text-slate-900">Mise en page</h2>
                  
                  <div className="space-y-6">
                    <div>
                      <label className="text-sm font-medium text-slate-700">Format de page</label>
                      <div className="mt-2 flex gap-2">
                        {['A4', 'A5'].map((size) => (
                          <button
                            key={size}
                            onClick={() => handleDesignChange('layout.page_size', size)}
                            className={cn(
                              "px-4 py-2 text-sm rounded-lg border transition-colors",
                              designConfig.layout.page_size === size
                                ? "bg-blue-100 border-blue-300 text-blue-700"
                                : "bg-white border-slate-300 text-slate-700 hover:bg-slate-50"
                            )}
                          >
                            {size}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="border-t border-slate-200 pt-6 space-y-4">
                      <h3 className="text-sm font-medium text-slate-700">Espacements</h3>
                      
                      <Slider
                        label="Espacement paragraphes"
                        value={designConfig.spacing.paragraph_gap_cm}
                        min={0}
                        max={2}
                        step={0.1}
                        onChange={(v) => handleDesignChange('spacing.paragraph_gap_cm', v)}
                        unit="cm"
                      />
                      
                      <Slider
                        label="Espacement sections"
                        value={designConfig.spacing.section_gap_cm}
                        min={0}
                        max={2}
                        step={0.1}
                        onChange={(v) => handleDesignChange('spacing.section_gap_cm', v)}
                        unit="cm"
                      />
                    </div>

                    <div className="border-t border-slate-200 pt-6 space-y-4">
                      <h3 className="text-sm font-medium text-slate-700">En-tête</h3>
                      
                      <label className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={designConfig.header.bilingual}
                          onChange={(e) => handleDesignChange('header.bilingual', e.target.checked)}
                          className="w-4 h-4 text-blue-600 rounded border-slate-300"
                        />
                        <span className="text-sm text-slate-700">Mode bilingue (FR/AR)</span>
                      </label>
                      
                      <label className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={designConfig.header.logo_in_header}
                          onChange={(e) => handleDesignChange('header.logo_in_header', e.target.checked)}
                          className="w-4 h-4 text-blue-600 rounded border-slate-300"
                        />
                        <span className="text-sm text-slate-700">Afficher le logo dans l'en-tête</span>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* WATERMARK */}
              {activeTab === 'watermark' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-semibold text-slate-900">Filigrane (Watermark)</h2>
                  
                  <div className="space-y-6">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={designConfig.watermark.enabled}
                        onChange={(e) => handleDesignChange('watermark.enabled', e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded border-slate-300"
                      />
                      <span className="text-sm text-slate-700">Activer le filigrane logo</span>
                    </label>
                    
                    {designConfig.watermark.enabled && (
                      <>
                        <Slider
                          label="Taille du logo"
                          value={designConfig.watermark.size_cm}
                          min={3}
                          max={10}
                          step={0.5}
                          onChange={(v) => handleDesignChange('watermark.size_cm', v)}
                          unit="cm"
                        />
                        
                        <Slider
                          label="Opacité"
                          value={designConfig.watermark.opacity}
                          min={0}
                          max={1}
                          step={0.05}
                          onChange={(v) => handleDesignChange('watermark.opacity', v)}
                        />
                        
                        <div>
                          <label className="text-sm font-medium text-slate-700">Position</label>
                          <select
                            value={designConfig.watermark.position}
                            onChange={(e) => handleDesignChange('watermark.position', e.target.value)}
                            className="mt-2 block w-full rounded-lg border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                          >
                            <option value="center">Centré</option>
                            <option value="top-left">Haut gauche</option>
                            <option value="top-right">Haut droite</option>
                            <option value="bottom-left">Bas gauche</option>
                            <option value="bottom-right">Bas droite</option>
                          </select>
                        </div>
                      </>
                    )}
                    
                    {!cabinet?.logo_url && (
                      <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                        <p className="text-sm text-orange-700">
                          ⚠️ Aucun logo configuré. Uploadez un logo dans les réglages du cabinet pour activer le filigrane.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateBuilder;
