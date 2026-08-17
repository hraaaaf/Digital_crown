import React, { useState } from 'react';
import { Shield, Database, Download, Loader2 } from 'lucide-react';
import { SettingsSection } from '../components/SharedUI';
import { MobileSecurity } from '../../Security/MobileSecurity';
import { AuditLogViewer } from '../../Security/AuditLogViewer';
import { api } from '../../../../services/api';
import toast from 'react-hot-toast';

const backupFilename = (contentDisposition?: string): string => {
  const match = contentDisposition?.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i);
  return match?.[1]?.replace(/\"/g, '').trim() || 'digital-crown-backup.enc';
};

export const SecurityTab: React.FC = () => {
  const [isExporting, setIsExporting] = useState(false);

  const handleExportDB = async () => {
    setIsExporting(true);
    try {
      const response = await api.get('/admin/export-db', { responseType: 'blob' });
      const filename = backupFilename(response.headers['content-disposition']);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/octet-stream' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success("Sauvegarde chiffrée créée et téléchargée");
    } catch (error) {
      toast.error("Impossible de créer une sauvegarde chiffrée vérifiée");
      console.error("Verified backup export error:", error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-12">
      <SettingsSection 
        title="Sécurité & Souveraineté" 
        subtitle="Contrôlez vos données cliniques et vos accès mobiles."
        icon={<Shield size={32} />}
      >
        <div className="bg-slate-50 border border-slate-200 rounded-[2.5rem] p-10 flex flex-col items-center justify-center text-center gap-6">
          <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center shadow-xl text-slate-700 border border-slate-100">
            <Database size={40} />
          </div>
          <div className="max-w-md">
            <h4 className="font-black text-xl text-slate-800">Sauvegarde chiffrée vérifiée</h4>
            <p className="text-sm text-slate-500 mt-2 font-medium">Crée une sauvegarde chiffrée du moteur de données actif, vérifie sa création puis télécharge le fichier avec son format réel.</p>
          </div>
          <button 
            onClick={handleExportDB}
            disabled={isExporting}
            className="px-10 py-5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-black transition-all shadow-2xl shadow-emerald-600/20 flex items-center gap-4 group hover:scale-[1.02] disabled:opacity-70 disabled:hover:scale-100 disabled:cursor-not-allowed"
          >
            {isExporting ? (
              <Loader2 size={24} className="animate-spin" />
            ) : (
              <Download size={24} className="group-hover:translate-y-1 transition-transform" /> 
            )}
            {isExporting ? "Création et vérification..." : "Créer et télécharger la sauvegarde"}
          </button>
        </div>

        <div className="pt-10 border-t border-slate-100">
           <MobileSecurity />
        </div>

        <div className="pt-10 border-t border-slate-100">
           <AuditLogViewer />
        </div>
      </SettingsSection>
    </div>
  );
};
