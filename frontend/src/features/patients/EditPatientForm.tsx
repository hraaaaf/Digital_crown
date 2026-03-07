import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { 
  ArrowLeft, 
  Save, 
  Loader2, 
  User, 
  Phone, 
  Calendar, 
  UserCircle 
} from 'lucide-react';


export const EditPatientForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    date_naissance: '',
    telephone: ''
  });

  // Chargement initial des données du patient
  useEffect(() => {
    const fetchPatient = async () => {
      try {
        setLoading(true);
        const res = await api.get(`/patients/${id}`);
        setFormData(res.data);
      } catch (err) {
        console.error("Erreur de récupération:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPatient();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      // Mise à jour via l'API
      await api.put(`/patients/${id}`, formData);
      // Retour immédiat à la fiche patient après succès
      navigate(`/patients/${id}`);
    } catch (err) {
      alert("Erreur lors de la sauvegarde.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div className="h-screen flex flex-col items-center justify-center gap-4 bg-slate-50">
      <Loader2 className="animate-spin text-[#003380]" size={48} />
      <p className="text-slate-400 font-black uppercase tracking-widest text-[10px]">Chargement du dossier...</p>
    </div>
  );

  const inputClass = "w-full px-6 py-4 bg-white/70 border border-slate-200 rounded-[1.5rem] focus:ring-4 focus:ring-[#003380]/10 focus:border-[#003380] outline-none transition-all font-bold text-[#003380] placeholder:text-slate-300";
  const labelClass = "text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] ml-5 mb-2 flex items-center gap-2";

  return (
    <div className="max-w-2xl mx-auto p-6 md:p-10 animate-in slide-in-from-bottom-6 duration-700">
      
      {/* BOUTON RETOUR : Cohérent avec PatientDetails */}
      <button 
        onClick={() => navigate(-1)} 
        className="flex items-center gap-2 text-slate-400 hover:text-[#003380] font-black text-xs uppercase tracking-widest mb-8 transition-colors group"
      >
        <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" /> 
        Retour au dossier
      </button>
      
      <div className="bg-white/70 backdrop-blur-2xl p-8 md:p-12 rounded-[2.5rem] border border-white/80 shadow-[0_20px_50px_rgba(0,0,0,0.05)]">
        
        <div className="flex items-center gap-6 mb-12">
          <div className="w-16 h-16 bg-[#003380] text-white rounded-3xl flex items-center justify-center shadow-xl shadow-[#003380]/20">
            <UserCircle size={32} strokeWidth={2} />
          </div>
          <div>
            <h2 className="text-3xl font-black text-[#003380] tracking-tight leading-none">Mise à jour</h2>
            <p className="text-slate-400 font-bold text-sm mt-2">Dossier Patient ID-{id}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className={labelClass}><User size={12}/> Nom</label>
              <input 
                type="text" 
                className={inputClass} 
                value={formData.nom} 
                onChange={(e) => setFormData({...formData, nom: e.target.value.toUpperCase()})} 
                required 
              />
            </div>
            <div>
              <label className={labelClass}><User size={12}/> Prénom</label>
              <input 
                type="text" 
                className={inputClass} 
                value={formData.prenom} 
                onChange={(e) => setFormData({...formData, prenom: e.target.value})} 
                required 
              />
            </div>
          </div>
          
          <div>
            <label className={labelClass}><Calendar size={12}/> Date de naissance</label>
            <input 
              type="date" 
              className={inputClass} 
              value={formData.date_naissance} 
              onChange={(e) => setFormData({...formData, date_naissance: e.target.value})} 
              required 
            />
          </div>

          <div>
            <label className={labelClass}><Phone size={12}/> Téléphone de contact</label>
            <input 
              type="tel" 
              className={inputClass} 
              value={formData.telephone} 
              onChange={(e) => setFormData({...formData, telephone: e.target.value})} 
              required 
            />
          </div>

          <div className="pt-4">
            <button 
              type="submit" 
              disabled={saving} 
              className="w-full py-5 bg-[#003380] text-white rounded-[1.5rem] font-black text-lg flex items-center justify-center gap-3 shadow-2xl shadow-[#003380]/30 hover:bg-blue-900 transition-all hover:-translate-y-1 active:scale-95 disabled:opacity-50"
            >
              {saving ? <Loader2 className="animate-spin" size={24} /> : <Save size={24} />} 
              {saving ? "Enregistrement..." : "Valider les modifications"}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};