/**
 * DocumentArchiveManager.tsx
 * Gestion intelligente des documents archivés avec :
 * - Détection des conflits
 * - Aperçu comparatif
 * - Corbeille avec récupération
 * - Versioning
 */
import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Archive, Trash2, RotateCcw, Eye, Download, History,
  AlertTriangle, CheckCircle, XCircle, FileText, Search,
  Filter, FolderOpen, Clock, Tag, AlertCircle
} from 'lucide-react';
import { api } from '../../services/api';

// Types
interface DocumentVersion {
  version_number: number;
  created_at: string;
  file_size: number;
  is_latest: boolean;
}

interface DocumentArchive {
  id: number;
  patient_id: number;
  document_type: DocumentType;
  filename: string;
  original_filename: string;
  title?: string;
  description?: string;
  tags: string[];
  file_size: number;
  version_number: number;
  is_latest_version: boolean;
  status: 'ACTIF' | 'SUPPRIME' | 'ARCHIVE';
  created_at: string;
  deleted_at?: string;
  permanent_delete_at?: string;
  download_url: string;
  all_versions?: DocumentVersion[];
}

type DocumentType = 
  | 'RAPPORT_CEPHALO' | 'ORDONNANCE' | 'CERTIFICAT' | 'DEVIS'
  | 'NOTE_HONORAIRES' | 'LETTRE_MEDICALE' | 'DOCUMENT_LIBRE'
  | 'PHOTO_CLINIQUE' | 'RADIOGRAPHIE' | 'MOULAGE' | 'AUTRE';

interface ConflictInfo {
  has_conflict: boolean;
  conflict_reason?: 'same_hash' | 'same_name_same_day' | 'recent_similar';
  suggested_action?: 'KEEP_BOTH' | 'OVERWRITE' | 'CANCEL' | 'CREATE_VERSION';
  message?: string;
  existing_document?: DocumentArchive;
}

interface ArchiveManagerProps {
  patientId: number;
}

// Configuration des couleurs
const PALETTE = {
  bgCard: 'var(--bg-card, #ffffff)',
  bgPanel: 'var(--bg-panel, #f8fafc)',
  border: 'var(--border, #e2e8f0)',
  text: 'var(--text, #1e293b)',
  textMuted: 'var(--text-muted, #64748b)',
  accent: 'var(--accent, #3b82f6)',
  accentSuccess: 'var(--accent-success, #10b981)',
  accentWarning: 'var(--accent-warning, #f59e0b)',
  accentError: 'var(--accent-error, #ef4444)',
};

// Helper pour formater la taille
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Helper pour formater la date
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Labels des types de documents
const DOC_TYPE_LABELS: Record<DocumentType, { label: string; color: string }> = {
  RAPPORT_CEPHALO: { label: 'Rapport Céphalo', color: '#3b82f6' },
  ORDONNANCE: { label: 'Ordonnance', color: '#10b981' },
  CERTIFICAT: { label: 'Certificat', color: '#8b5cf6' },
  DEVIS: { label: 'Devis', color: '#f59e0b' },
  NOTE_HONORAIRES: { label: 'Note Honoraires', color: '#ef4444' },
  LETTRE_MEDICALE: { label: 'Lettre Médicale', color: '#06b6d4' },
  DOCUMENT_LIBRE: { label: 'Document Libre', color: '#6b7280' },
  PHOTO_CLINIQUE: { label: 'Photo Clinique', color: '#ec4899' },
  RADIOGRAPHIE: { label: 'Radiographie', color: '#14b8a6' },
  MOULAGE: { label: 'Moulage', color: '#84cc16' },
  AUTRE: { label: 'Autre', color: '#64748b' },
};

// Composant principal
export const DocumentArchiveManager: React.FC<ArchiveManagerProps> = ({ patientId }) => {
  const [documents, setDocuments] = useState<DocumentArchive[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<DocumentType | ''>('');
  const [showTrash, setShowTrash] = useState(false);
  // const [selectedDoc, setSelectedDoc] = useState<DocumentArchive | null>(null);
  const [expandedVersions, setExpandedVersions] = useState<number | null>(null);
  
  // Modal de conflit
  const [conflictModal, setConflictModal] = useState<{
    isOpen: boolean;
    conflict?: ConflictInfo;
    pendingUpload?: File;
  }>({ isOpen: false });
  
  // Notification toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' } | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'warning') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  // Charger les documents
  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/documents', {
        params: {
          patient_id: patientId,
          doc_type: filterType || undefined,
          status: showTrash ? 'SUPPRIME' : 'ACTIF',
          search: searchQuery || undefined,
          page_size: 50
        }
      });
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Erreur chargement documents:', error);
      showToast('Erreur lors du chargement des documents', 'error');
    } finally {
      setLoading(false);
    }
  }, [patientId, filterType, showTrash, searchQuery, showToast]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  /* 
   * Upload avec détection de conflits (préparé pour intégration future)
   * Pour l'instant, les documents sont archivés automatiquement lors de la génération
   * 
  const _handleUpload = useCallback(async (file: File, docType: DocumentType) => {
    // ... implémentation future
  }, [patientId, showToast, performUpload]);
  */

  // Upload effectif
  const performUpload = useCallback(async (
    file: File,
    docType: DocumentType,
    resolution: string,
    title?: string,
    description?: string,
    tags: string[] = []
  ) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);
    formData.append('on_conflict', resolution);
    formData.append('title', title || file.name);
    formData.append('description', description || '');
    formData.append('tags', JSON.stringify(tags));

    try {
      const response = await api.post(`/documents/archive?patient_id=${patientId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.success) {
        showToast(response.data.message, 'success');
        loadDocuments();
      } else if (response.data.requires_action) {
        // Conflit détecté côté serveur
        setConflictModal({
          isOpen: true,
          conflict: response.data.conflict_info,
          pendingUpload: file
        });
      }
    } catch (error: any) {
      console.error('Erreur upload:', error);
      showToast(error.response?.data?.detail || 'Erreur lors du téléchargement', 'error');
    }
  }, [patientId, loadDocuments, showToast]);

  // Déplacer vers corbeille
  const moveToTrash = useCallback(async (docId: number) => {
    if (!confirm('Déplacer ce document dans la corbeille ?')) return;
    
    try {
      await api.post(`/documents/${docId}/trash`);
      showToast('Document déplacé dans la corbeille', 'warning');
      loadDocuments();
    } catch (error) {
      showToast('Erreur lors de la suppression', 'error');
    }
  }, [loadDocuments, showToast]);

  // Restaurer depuis corbeille
  const restoreFromTrash = useCallback(async (docId: number) => {
    try {
      await api.post(`/documents/${docId}/restore`);
      showToast('Document restauré avec succès', 'success');
      loadDocuments();
    } catch (error) {
      showToast('Erreur lors de la restauration', 'error');
    }
  }, [loadDocuments, showToast]);

  // Suppression définitive
  const permanentDelete = useCallback(async (docId: number) => {
    if (!confirm('ATTENTION: Cette action est irréversible !\n\nLe document sera supprimé définitivement.')) return;
    
    try {
      await api.delete(`/documents/${docId}?confirm=true`);
      showToast('Document supprimé définitivement', 'success');
      loadDocuments();
    } catch (error) {
      showToast('Erreur lors de la suppression définitive', 'error');
    }
  }, [loadDocuments, showToast]);

  // Télécharger
  const downloadDocument = useCallback(async (doc: DocumentArchive, version?: number) => {
    try {
      const response = await api.get(`/documents/${doc.id}/download`, {
        params: version ? { version } : {},
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = doc.original_filename;
      link.click();
      URL.revokeObjectURL(url);
      
      showToast('Téléchargement démarré', 'success');
    } catch (error) {
      showToast('Erreur lors du téléchargement', 'error');
    }
  }, [showToast]);

  // Aperçu
  const previewDocument = useCallback(async (doc: DocumentArchive) => {
    try {
      const response = await api.get(`/documents/${doc.id}/download`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (error) {
      showToast('Erreur lors de l\'ouverture', 'error');
    }
  }, [showToast]);

  return (
    <div className="flex flex-col gap-4 p-4" style={{ background: PALETTE.bgPanel }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Archive size={24} style={{ color: PALETTE.accent }} />
          <h2 className="text-xl font-bold" style={{ color: PALETTE.text }}>
            {showTrash ? 'Corbeille' : 'Documents Archivés'}
          </h2>
          <span className="px-2 py-1 rounded-full text-xs" 
                style={{ background: PALETTE.bgPanel, color: PALETTE.textMuted }}>
            {documents.length} document{documents.length > 1 ? 's' : ''}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowTrash(!showTrash)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all"
            style={{ 
              background: showTrash ? `${PALETTE.accentError}15` : PALETTE.bgCard,
              border: `1px solid ${showTrash ? PALETTE.accentError : PALETTE.border}`,
              color: showTrash ? PALETTE.accentError : PALETTE.text
            }}
          >
            {showTrash ? <FolderOpen size={16} /> : <Trash2 size={16} />}
            {showTrash ? 'Documents actifs' : 'Corbeille'}
          </button>
        </div>
      </div>

      {/* Barre de recherche et filtres */}
      <div className="flex flex-wrap items-center gap-3 p-3 rounded-xl" style={{ background: PALETTE.bgCard }}>
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <Search size={16} style={{ color: PALETTE.textMuted }} />
          <input
            type="text"
            placeholder="Rechercher un document..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-transparent outline-none text-sm"
            style={{ color: PALETTE.text }}
          />
        </div>
        
        <div className="flex items-center gap-2">
          <Filter size={16} style={{ color: PALETTE.textMuted }} />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as DocumentType | '')}
            className="px-3 py-2 rounded-lg text-sm outline-none"
            style={{ background: PALETTE.bgPanel, border: `1px solid ${PALETTE.border}`, color: PALETTE.text }}
          >
            <option value="">Tous les types</option>
            {Object.entries(DOC_TYPE_LABELS).map(([type, { label }]) => (
              <option key={type} value={type}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Liste des documents */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: PALETTE.accent }} />
        </div>
      ) : documents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 gap-4" 
             style={{ color: PALETTE.textMuted }}>
          <Archive size={48} opacity={0.3} />
          <p>{showTrash ? 'La corbeille est vide' : 'Aucun document archivé'}</p>
          {!showTrash && (
            <p className="text-sm">Les documents générés apparaîtront ici automatiquement</p>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 rounded-xl transition-all hover:shadow-md"
              style={{ background: PALETTE.bgCard, border: `1px solid ${PALETTE.border}` }}
            >
              <div className="flex items-start gap-4">
                {/* Icône type */}
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: `${DOC_TYPE_LABELS[doc.document_type].color}15` }}
                >
                  <FileText size={20} style={{ color: DOC_TYPE_LABELS[doc.document_type].color }} />
                </div>
                
                {/* Info document */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-medium truncate" style={{ color: PALETTE.text }}>
                      {doc.title || doc.original_filename}
                    </h3>
                    {doc.is_latest_version && doc.version_number > 1 && (
                      <span className="px-2 py-0.5 rounded text-xs" 
                            style={{ background: `${PALETTE.accent}15`, color: PALETTE.accent }}>
                        v{doc.version_number}
                      </span>
                    )}
                    {doc.status === 'SUPPRIME' && (
                      <span className="px-2 py-0.5 rounded text-xs" 
                            style={{ background: `${PALETTE.accentError}15`, color: PALETTE.accentError }}>
                        Supprimé
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-4 mt-1 text-xs" style={{ color: PALETTE.textMuted }}>
                    <span>{DOC_TYPE_LABELS[doc.document_type].label}</span>
                    <span>•</span>
                    <span>{formatFileSize(doc.file_size)}</span>
                    <span>•</span>
                    <span>{formatDate(doc.created_at)}</span>
                    
                    {doc.permanent_delete_at && (
                      <>
                        <span>•</span>
                        <span style={{ color: PALETTE.accentWarning }}>
                          <Clock size={12} className="inline mr-1" />
                          Suppression définitive le {new Date(doc.permanent_delete_at).toLocaleDateString('fr-FR')}
                        </span>
                      </>
                    )}
                  </div>
                  
                  {doc.tags && doc.tags.length > 0 && (
                    <div className="flex items-center gap-1 mt-2 flex-wrap">
                      {doc.tags.map((tag, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-xs flex items-center gap-1"
                              style={{ background: PALETTE.bgPanel, color: PALETTE.textMuted }}>
                          <Tag size={10} />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Actions */}
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => previewDocument(doc)}
                    className="p-2 rounded-lg transition-colors hover:bg-gray-100"
                    title="Aperçu"
                  >
                    <Eye size={16} style={{ color: PALETTE.textMuted }} />
                  </button>
                  
                  <button
                    onClick={() => downloadDocument(doc)}
                    className="p-2 rounded-lg transition-colors hover:bg-gray-100"
                    title="Télécharger"
                  >
                    <Download size={16} style={{ color: PALETTE.textMuted }} />
                  </button>
                  
                  {doc.is_latest_version && (
                    <button
                      onClick={() => setExpandedVersions(expandedVersions === doc.id ? null : doc.id)}
                      className="p-2 rounded-lg transition-colors hover:bg-gray-100"
                      title="Historique des versions"
                    >
                      <History size={16} style={{ color: PALETTE.textMuted }} />
                    </button>
                  )}
                  
                  {showTrash ? (
                    <>
                      <button
                        onClick={() => restoreFromTrash(doc.id)}
                        className="p-2 rounded-lg transition-colors hover:bg-green-50"
                        title="Restaurer"
                      >
                        <RotateCcw size={16} style={{ color: PALETTE.accentSuccess }} />
                      </button>
                      <button
                        onClick={() => permanentDelete(doc.id)}
                        className="p-2 rounded-lg transition-colors hover:bg-red-50"
                        title="Supprimer définitivement"
                      >
                        <XCircle size={16} style={{ color: PALETTE.accentError }} />
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => moveToTrash(doc.id)}
                      className="p-2 rounded-lg transition-colors hover:bg-red-50"
                      title="Déplacer vers la corbeille"
                    >
                      <Trash2 size={16} style={{ color: PALETTE.accentError }} />
                    </button>
                  )}
                </div>
              </div>
              
              {/* Historique des versions */}
              <AnimatePresence>
                {expandedVersions === doc.id && doc.all_versions && doc.all_versions.length > 1 && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-4 pt-4 border-t"
                    style={{ borderColor: PALETTE.border }}
                  >
                    <h4 className="text-sm font-medium mb-3" style={{ color: PALETTE.textMuted }}>
                      Historique des versions
                    </h4>
                    <div className="space-y-2">
                      {doc.all_versions.map((version) => (
                        <div 
                          key={version.version_number}
                          className="flex items-center justify-between p-2 rounded-lg"
                          style={{ background: PALETTE.bgPanel }}
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-medium" style={{ color: PALETTE.text }}>
                              v{version.version_number}
                            </span>
                            {version.is_latest && (
                              <span className="px-2 py-0.5 rounded text-xs" 
                                    style={{ background: `${PALETTE.accent}15`, color: PALETTE.accent }}>
                                Actuelle
                              </span>
                            )}
                            <span className="text-xs" style={{ color: PALETTE.textMuted }}>
                              {formatDate(version.created_at)}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs" style={{ color: PALETTE.textMuted }}>
                              {formatFileSize(version.file_size)}
                            </span>
                            {!version.is_latest && (
                              <button
                                onClick={() => downloadDocument(doc, version.version_number)}
                                className="p-1.5 rounded hover:bg-gray-200"
                              >
                                <Download size={14} style={{ color: PALETTE.textMuted }} />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      )}

      {/* Modal de résolution de conflit */}
      <AnimatePresence>
        {conflictModal.isOpen && conflictModal.conflict && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="max-w-lg w-full p-6 rounded-2xl shadow-2xl"
              style={{ background: PALETTE.bgCard }}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-full" style={{ background: `${PALETTE.accentWarning}15` }}>
                  <AlertTriangle size={24} style={{ color: PALETTE.accentWarning }} />
                </div>
                <h3 className="text-lg font-bold" style={{ color: PALETTE.text }}>
                  Conflit détecté
                </h3>
              </div>
              
              <p className="mb-4" style={{ color: PALETTE.textMuted }}>
                {conflictModal.conflict.message}
              </p>
              
              {conflictModal.conflict.existing_document && (
                <div className="p-4 rounded-xl mb-4" style={{ background: PALETTE.bgPanel }}>
                  <h4 className="text-sm font-medium mb-2" style={{ color: PALETTE.text }}>
                    Document existant:
                  </h4>
                  <p className="text-sm" style={{ color: PALETTE.textMuted }}>
                    <strong>{conflictModal.conflict.existing_document.original_filename}</strong>
                  </p>
                  <p className="text-xs mt-1" style={{ color: PALETTE.textMuted }}>
                    Créé le {formatDate(conflictModal.conflict.existing_document.created_at)}
                  </p>
                  <p className="text-xs" style={{ color: PALETTE.textMuted }}>
                    Taille: {formatFileSize(conflictModal.conflict.existing_document.file_size)}
                  </p>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-3 mt-6">
                <button
                  onClick={() => {
                    setConflictModal({ isOpen: false });
                    if (conflictModal.pendingUpload) {
                      performUpload(
                        conflictModal.pendingUpload,
                        'RAPPORT_CEPHALO',
                        'CANCEL'
                      );
                    }
                  }}
                  className="px-4 py-3 rounded-xl text-sm font-medium transition-colors"
                  style={{ background: PALETTE.bgPanel, color: PALETTE.text }}
                >
                  Annuler
                </button>
                
                <button
                  onClick={() => {
                    setConflictModal({ isOpen: false });
                    if (conflictModal.pendingUpload) {
                      performUpload(
                        conflictModal.pendingUpload,
                        'RAPPORT_CEPHALO',
                        'CREATE_VERSION'
                      );
                    }
                  }}
                  className="px-4 py-3 rounded-xl text-sm font-medium transition-colors"
                  style={{ background: PALETTE.accent, color: 'white' }}
                >
                  Créer une version
                </button>
                
                <button
                  onClick={() => {
                    setConflictModal({ isOpen: false });
                    if (conflictModal.pendingUpload) {
                      performUpload(
                        conflictModal.pendingUpload,
                        'RAPPORT_CEPHALO',
                        'KEEP_BOTH'
                      );
                    }
                  }}
                  className="px-4 py-3 rounded-xl text-sm font-medium transition-colors col-span-2"
                  style={{ background: `${PALETTE.accentSuccess}15`, color: PALETTE.accentSuccess, border: `1px solid ${PALETTE.accentSuccess}` }}
                >
                  Garder les deux (renommer)
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toast notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-6 right-6 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg"
            style={{ 
              background: toast.type === 'success' ? PALETTE.accentSuccess 
                        : toast.type === 'error' ? PALETTE.accentError 
                        : PALETTE.accentWarning,
              color: 'white'
            }}
          >
            {toast.type === 'success' ? <CheckCircle size={18} />
             : toast.type === 'error' ? <AlertCircle size={18} />
             : <AlertTriangle size={18} />}
            <span className="text-sm font-medium">{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default DocumentArchiveManager;
