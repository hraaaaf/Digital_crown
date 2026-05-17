import React, { useState, useEffect, useRef } from 'react';
import { X, Clock, User, FileText, Search, Plus, Check, MessageCircle, Calendar, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import type { AppointmentStatus } from './DailyView';
import { cn } from '../../utils/cn';
import { useClinicalRef } from '../clinical-ref/useClinicalRef';
import { ClinicalRefSidebar } from '../clinical-ref/ClinicalRefSidebar';
import { useEliteStore } from '../../stores/useEliteStore';

interface Patient {
  id: number;
  nom: string;
  prenom: string;
  numero_dossier?: string;
}

interface ClinicalAct {
  id: number;
  name: string;
  base_price: number;
}

interface AgendaModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
  selectedDate: Date | null;
  initialTime?: string;
  editingAppointment?: any;
}

export const AgendaModal: React.FC<AgendaModalProps> = ({ isOpen, onClose, onSaved, selectedDate, initialTime, editingAppointment }) => {
  const { fetchPatientIntelligence } = useEliteStore();
  const [patientSearch, setPatientSearch] = useState('');
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientsList, setPatientsList] = useState<Patient[]>([]);
  const [showPatientResults, setShowPatientResults] = useState(false);

  
  const [actSearch, setActSearch] = useState('');
  const [selectedAct, setSelectedAct] = useState<ClinicalAct | null>(null);
  const [actsList, setActsList] = useState<ClinicalAct[]>([]);
  const [showActResults, setShowActResults] = useState(false);

  const [motif, setMotif] = useState('');
  const [time, setTime] = useState(initialTime || '09:00');
  const [duration, setDuration] = useState(30);
  const [status, setStatus] = useState<AppointmentStatus>('PRÉVU');
  const [loading, setLoading] = useState(false);
  const [dateValue, setDateValue] = useState('');
  const [smartIntel, setSmartIntel] = useState<any>(null);
  const [loadingIntel, setLoadingIntel] = useState(false);
  
  const protocol = useClinicalRef(selectedAct?.name || actSearch);
  const [showClinicalRef, setShowClinicalRef] = useState(false);

  useEffect(() => {
    if (protocol) {
      setShowClinicalRef(true);
    } else {
      setShowClinicalRef(false);
    }
  }, [protocol]);


  useEffect(() => {
    if (isOpen) {
      if (editingAppointment) {
        const d = new Date(editingAppointment.datetime_start);
        setDateValue(d.toISOString().split('T')[0]);
        setTime(`${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`);
        setDuration(editingAppointment.duration_minutes);
        setMotif(editingAppointment.motif || '');
        setActSearch(editingAppointment.motif || '');
        setStatus(editingAppointment.status);
        if (editingAppointment.patient_id) {
           setSelectedPatient({ id: editingAppointment.patient_id, nom: editingAppointment.patient_name?.split(' ')[0] || '', prenom: editingAppointment.patient_name?.split(' ')[1] || '' });
        }
      } else {
        setDateValue(selectedDate ? selectedDate.toISOString().split('T')[0] : new Date().toISOString().split('T')[0]);
        setTime(initialTime || '09:00');
        setDuration(30);
        setMotif('');
        setActSearch('');
        setSelectedPatient(null);
        setStatus('PRÉVU');
      }
    }
  }, [isOpen, editingAppointment, initialTime, selectedDate]);


  const patientRef = useRef<HTMLDivElement>(null);
  const actRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (patientSearch.length > 1 && !selectedPatient) {
      const fetchPatients = async () => {
        try {
          const res = await api.get('/patients/', { params: { limit: 10, search: patientSearch } });
          const filtered = res.data.filter((p: Patient) => 
            `${p.nom} ${p.prenom}`.toLowerCase().includes(patientSearch.toLowerCase()) ||
            p.numero_dossier?.toLowerCase().includes(patientSearch.toLowerCase())
          );
          setPatientsList(filtered.length > 0 ? filtered : res.data);
          setShowPatientResults(true);
        } catch (e) {
          console.error(e);
        }
      };
      fetchPatients();
    } else {
      setShowPatientResults(false);
    }
  }, [patientSearch, selectedPatient]);

  useEffect(() => {
    if (selectedPatient) {
      setLoadingIntel(true);
      // 1. Récupération des suggestions d'agenda locales
      api.get(`/patients/${selectedPatient.id}/appointment-intel`)
        .then(res => setSmartIntel(res.data))
        .catch(e => console.error(e))
        .finally(() => setLoadingIntel(false));
      
      // 2. Synchronisation globale avec le Ghost Hub Brain
      fetchPatientIntelligence(selectedPatient.id).catch(e => console.error(e));
    } else {
      setSmartIntel(null);
    }
  }, [selectedPatient, fetchPatientIntelligence]);

  const applySmartIntel = () => {
    if (smartIntel) {
      setMotif(smartIntel.suggestion);
      setDuration(smartIntel.duration);
      if (!selectedAct) {
          setActSearch(smartIntel.suggestion);
      }
    }
  };

  const openWhatsApp = () => {
    if (!selectedPatient) return;
    const dateStr = selectedDate?.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
    const msg = `Bonjour ${selectedPatient.prenom}, votre rendez-vous pour ${motif || actSearch || 'votre soin'} est confirmé pour le ${dateStr} à ${time}. À bientôt !`;
    window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`, '_blank');
  };


  useEffect(() => {
    const fetchActs = async () => {
      try {
        const res = await api.get('/actes/catalog/search', { params: { q: actSearch } });
        setActsList(res.data);
      } catch (e) {
        console.error(e);
      }
    };
    if (isOpen && !selectedAct) {
      fetchActs();
    }
  }, [actSearch, selectedAct, isOpen]);

  useEffect(() => {
    const actName = selectedAct ? selectedAct.name : actSearch;
    if (actName && actName.trim().length > 1) {
      const fetchRecommendedDuration = async () => {
        try {
          const res = await api.get('/actes/duration', { params: { q: actName } });
          if (res.data && res.data.duration) {
            setDuration(res.data.duration);
          }
        } catch (e) {
          console.error(e);
        }
      };
      const timer = setTimeout(() => {
        fetchRecommendedDuration();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [selectedAct, actSearch]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (patientRef.current && !patientRef.current.contains(event.target as Node)) setShowPatientResults(false);
      if (actRef.current && !actRef.current.contains(event.target as Node)) setShowActResults(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDate) return;
    
    setLoading(true);
    try {
      const [hours, minutes] = time.split(':').map(Number);
      const startDateTime = new Date(dateValue);
      startDateTime.setHours(hours, minutes, 0, 0);

      const payload = {
        patient_id: selectedPatient?.id || null,
        patient_name: selectedPatient ? `${selectedPatient.nom} ${selectedPatient.prenom}` : patientSearch,
        motif: selectedAct ? selectedAct.name : (motif || actSearch),
        datetime_start: startDateTime.toISOString(),
        duration_minutes: duration,
        status: status
      };

      if (editingAppointment) {
          await api.put(`/appointments/${editingAppointment.id}`, payload);
      } else {
          await api.post('/appointments/', payload);
      }

      onSaved();
      onClose();
      // Reset
      setPatientSearch('');
      setSelectedPatient(null);
      setActSearch('');
      setSelectedAct(null);
      setMotif('');
      setTime('09:00');
      setDuration(30);
      setStatus('PRÉVU');
    } catch (err) {
      console.error("Erreur saving appt", err);
      alert("Erreur lors de la création du rendez-vous.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[100] flex items-center justify-center p-4 animate-in fade-in duration-300">
      <div className="bg-white/90 backdrop-blur-2xl rounded-[2.5rem] shadow-2xl w-full max-w-xl overflow-hidden animate-in zoom-in-95 duration-300 border border-white">
        
        <div className="flex justify-between items-center p-8 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-500 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              {editingAppointment ? <Clock size={24} /> : <Plus size={24} />}
            </div>
            <div>
              <h2 className="text-2xl font-black text-[#003380] tracking-tight">
                  {editingAppointment ? "Modifier le Rendez-vous" : "Nouveau Rendez-vous"}
              </h2>
              <p className="text-slate-500 text-sm font-bold">Planification clinique</p>
            </div>
          </div>
          <button onClick={onClose} className="p-3 bg-white text-slate-400 hover:text-rose-500 rounded-full shadow-sm border border-slate-100 transition-all hover:rotate-90">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
          <div className="space-y-6">
            
            {/* PATIENT SEARCH */}
            <div className="relative" ref={patientRef}>
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3 ml-1">Patient</label>
              <div className="relative group">
                {selectedPatient ? (
                  <div className="w-full flex items-center justify-between pl-12 pr-4 py-4 bg-blue-50/50 border-2 border-blue-500 rounded-2xl text-sm font-black text-[#003380]">
                    <div className="flex items-center gap-2">
                      <User className="absolute left-4 text-blue-500" size={20} />
                      <span>{selectedPatient.nom} {selectedPatient.prenom}</span>
                      <span className="text-[10px] bg-blue-200 px-1.5 py-0.5 rounded text-blue-700">{selectedPatient.numero_dossier}</span>
                    </div>
                    <button type="button" onClick={() => setSelectedPatient(null)} className="text-blue-400 hover:text-rose-500 transition-colors">
                      <X size={18} />
                    </button>
                  </div>
                ) : (
                  <>
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18} />
                    <input 
                      type="text" 
                      required
                      placeholder="Rechercher ou saisir un nom..."
                      value={patientSearch}
                      onChange={e => setPatientSearch(e.target.value)}
                      className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-bold text-slate-700 outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:bg-white transition-all"
                    />
                  </>
                )}
              </div>
              
              {showPatientResults && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-2xl border border-slate-100 z-[110] max-h-60 overflow-y-auto animate-in slide-in-from-top-2 duration-200">
                  {patientsList.length > 0 ? patientsList.map(p => (
                    <button 
                      key={p.id}
                      type="button"
                      onClick={() => { setSelectedPatient(p); setShowPatientResults(false); }}
                      className="w-full flex items-center gap-4 px-6 py-4 hover:bg-slate-50 transition-colors border-b border-slate-50 last:border-0"
                    >
                      <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center text-slate-400 font-black">{p.nom[0]}</div>
                      <div className="text-left">
                        <div className="text-sm font-black text-slate-700">{p.nom} {p.prenom}</div>
                        <div className="text-[10px] font-bold text-slate-400">Dossier: {p.numero_dossier}</div>
                      </div>
                      <Check className="ml-auto text-emerald-500 opacity-0 group-hover:opacity-100" size={18} />
                    </button>
                  )) : (
                    <div className="p-6 text-center">
                      <p className="text-sm text-slate-400 font-bold mb-2">Aucun patient trouvé</p>
                      <button type="button" onClick={() => setShowPatientResults(false)} className="text-xs text-blue-500 font-black uppercase tracking-widest">Créer Patient Externe</button>
                    </div>
                  )}
                </div>
              )}
              {/* SMART INTEL CARD */}
              {(selectedPatient && (smartIntel || loadingIntel)) && (
                <div className="mt-4 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl animate-in slide-in-from-top-4 duration-300">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2 text-[#003380]">
                      <div className="w-6 h-6 bg-blue-500 rounded-lg flex items-center justify-center text-white">
                        {loadingIntel ? <RefreshCw size={14} className="animate-spin" /> : <Plus size={14} />}
                      </div>
                      <span className="text-[10px] font-black uppercase tracking-wider">
                        {loadingIntel ? "Analyse clinique..." : "Intelligence Clinique"}
                      </span>
                    </div>
                    {smartIntel?.solde_attente > 0 && (
                      <span className="bg-rose-100 text-rose-600 px-2 py-0.5 rounded text-[10px] font-black italic">
                        RESTE À PAYER : {smartIntel.solde_attente} MAD
                      </span>
                    )}
                  </div>
                  
                  {loadingIntel ? (
                    <div className="h-10 flex items-center justify-center">
                        <div className="flex gap-1">
                            <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce"></div>
                            <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                            <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                        </div>
                    </div>
                  ) : smartIntel && (
                    <div className="flex items-center justify-between">
                      <div>
                          <p className="text-xs font-bold text-slate-600 mb-1">Motif suggéré : <span className="text-[#003380]">{smartIntel.suggestion}</span></p>
                          <p className="text-[10px] text-slate-400">Basé sur le dernier devis actif</p>
                      </div>
                      <button 
                        type="button"
                        onClick={applySmartIntel}
                        className="px-3 py-1.5 bg-blue-600 text-white text-[10px] font-black rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                      >
                        APPLIQUER
                      </button>
                    </div>
                  )}
                </div>
              )}

            </div>


            {/* ACT / MOTIF SEARCH */}
            <div className="relative" ref={actRef}>
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3 ml-1">Acte / Motif</label>
              <div className="relative group">
                {selectedAct ? (
                  <div className="w-full flex items-center justify-between pl-12 pr-4 py-4 bg-emerald-50/50 border-2 border-emerald-500 rounded-2xl text-sm font-black text-emerald-700">
                    <div className="flex items-center gap-2">
                      <FileText className="absolute left-4 text-emerald-500" size={20} />
                      <span>{selectedAct.name}</span>
                      <span className="text-[10px] bg-emerald-200 px-1.5 py-0.5 rounded text-emerald-700">{selectedAct.base_price} MAD</span>
                    </div>
                    <button type="button" onClick={() => setSelectedAct(null)} className="text-emerald-400 hover:text-rose-500 transition-colors">
                      <X size={18} />
                    </button>
                  </div>
                ) : (
                  <>
                    <FileText className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18} />
                    <input 
                      type="text" 
                      required
                      placeholder="Saisir l'acte ou rechercher dans le catalogue..."
                      value={actSearch}
                      onChange={e => setActSearch(e.target.value)}
                      onFocus={() => setShowActResults(true)}
                      className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-bold text-slate-700 outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:bg-white transition-all"
                    />
                  </>
                )}
              </div>
              
              {showActResults && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-2xl border border-slate-100 z-[110] max-h-60 overflow-y-auto animate-in slide-in-from-top-2 duration-200">
                  {actsList.map(act => (
                    <button 
                      key={act.id}
                      type="button"
                      onClick={() => { setSelectedAct(act); setShowActResults(false); }}
                      className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 transition-colors border-b border-slate-50 last:border-0"
                    >
                      <div className="text-left">
                        <div className="text-sm font-black text-slate-700">{act.name}</div>
                      </div>
                      <div className="text-xs font-black text-emerald-600">{act.base_price} MAD</div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3 ml-1">Date</label>
                <div className="relative">
                  <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                  <input 
                    type="date" 
                    required
                    value={dateValue}
                    onChange={e => setDateValue(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-black text-[#003380] outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all font-mono"
                  />
                </div>
              </div>
              
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3 ml-1">Début</label>
                <div className="relative">
                  <Clock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                  <input 
                    type="time" 
                    required
                    value={time}
                    onChange={e => setTime(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-black text-[#003380] outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3 ml-1">Durée Prévue</label>
              <select 
                value={duration} 
                onChange={e => setDuration(Number(e.target.value))}
                className="w-full px-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-black text-slate-700 outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all appearance-none"
              >
                <option value={15}>15 min (Contrôle)</option>
                <option value={30}>30 min (Standard)</option>
                <option value={45}>45 min</option>
                <option value={60}>1 heure (Soin long)</option>
                <option value={90}>1h30 (Chirurgie)</option>
                <option value={120}>2 heures</option>
              </select>
            </div>


            <div>
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3 ml-1">Statut Initial</label>
              <div className="grid grid-cols-3 gap-3">
                {['PRÉVU', 'EN_S_ATTENTE', 'ANNULÉ'].map(s => (
                  <button 
                    key={s}
                    type="button"
                    onClick={() => setStatus(s as AppointmentStatus)}
                    className={cn(
                      "py-3 px-2 rounded-xl text-[10px] font-black uppercase tracking-tighter transition-all border",
                      status === s 
                        ? "bg-[#003380] text-white border-[#003380] shadow-lg shadow-blue-900/20" 
                        : "bg-white text-slate-500 border-slate-100 hover:border-slate-300"
                    )}
                  >
                    {s === 'EN_S_ATTENTE' ? 'SALLE ATTENTE' : s}
                  </button>
                ))}
              </div>
            </div>

          </div>

          <div className="pt-8 flex justify-between items-center border-t border-slate-100">
            {selectedPatient && (
                <button 
                    type="button" 
                    onClick={openWhatsApp}
                    className="flex items-center gap-2 text-emerald-600 hover:text-emerald-700 font-black text-xs transition-colors"
                >
                    <MessageCircle size={16} /> Rappel WhatsApp
                </button>
            )}
            <div className="flex gap-4">
                <button type="button" onClick={onClose} className="px-8 py-4 text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-2xl font-black transition-all">
                Annuler
                </button>
                <button 
                type="submit" 
                disabled={loading} 
                className="px-10 py-4 bg-gradient-to-r from-[#003380] to-[#0055d4] text-white rounded-2xl font-black hover:shadow-2xl hover:shadow-blue-900/30 hover:-translate-y-1 transition-all flex items-center gap-3 disabled:opacity-50"
                >
                {loading ? (
                    <> <Clock className="animate-spin" size={20} /> Création... </>
                ) : (
                    <> <Check size={20} /> {editingAppointment ? "Modifier le RDV" : "Confirmer le RDV"} </>
                )}
                </button>
            </div>
          </div>

        </form>
      </div>

      {protocol && (
        <ClinicalRefSidebar 
          protocol={protocol} 
          isOpen={showClinicalRef} 
          onClose={() => setShowClinicalRef(false)} 
        />
      )}
    </div>
  );
};
