import React, { useState, useEffect } from 'react';
import { Clock, Calendar, Ticket } from 'lucide-react';
import { api } from '../../../../services/api';
import { toast } from 'react-hot-toast';

export const AgendaTab: React.FC = () => {
  const [settings, setSettings] = useState({
    opening_time_morning: '09:00',
    closing_time_morning: '13:00',
    opening_time_afternoon: '14:00',
    closing_time_afternoon: '18:00',
    is_continuous: false,
    agenda_mode: 'EXACT',
    use_tickets: false
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await api.get('/agenda/settings');
        setSettings(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/agenda/settings', settings);
      toast.success('Paramètres Agenda sauvegardés !');
    } catch (err) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Chargement...</div>;

  const timeInputClass = 'min-w-0 w-full bg-slate-50 border-none rounded-xl p-4 font-bold text-slate-700';

  return (
    <div className="space-y-12 min-w-0">
      <div>
        <h2 className="text-2xl sm:text-3xl font-black text-slate-900 flex items-center gap-3 sm:gap-4">
          <Calendar className="text-primary shrink-0" size={32} />
          Horaires & Agenda
        </h2>
        <p className="text-slate-500 font-medium mt-2">
          Configurez votre emploi du temps et le mode de fonctionnement de votre cabinet.
        </p>
      </div>

      <div className="bg-white rounded-[2rem] p-5 sm:p-8 border border-slate-100 shadow-sm space-y-8 min-w-0">
        <h3 className="text-xl font-bold flex items-center gap-3">
          <Clock className="text-blue-500 shrink-0" />
          Horaires d'Ouverture
        </h3>

        <div className="flex items-start sm:items-center gap-4">
          <input
            type="checkbox"
            id="is_continuous"
            name="is_continuous"
            checked={settings.is_continuous}
            onChange={handleChange}
            className="w-6 h-6 shrink-0 rounded-xl border-slate-200 text-primary focus:ring-primary"
          />
          <label htmlFor="is_continuous" className="font-bold text-slate-700 leading-snug">Journée Continue (Sans pause de midi)</label>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 xl:gap-8 min-w-0">
          <div className="space-y-4 min-w-0">
            <h4 className="font-bold text-slate-500 uppercase tracking-widest text-xs">
              {settings.is_continuous ? "Heure d'ouverture" : 'Matin'}
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2 sm:gap-4 min-w-0">
              <input type="time" name="opening_time_morning" value={settings.opening_time_morning} onChange={handleChange} className={timeInputClass} />
              <span className="font-bold text-slate-400 text-center">à</span>
              <input type="time" name="closing_time_morning" value={settings.closing_time_morning} onChange={handleChange} className={timeInputClass} />
            </div>
          </div>

          {!settings.is_continuous && (
            <div className="space-y-4 min-w-0">
              <h4 className="font-bold text-slate-500 uppercase tracking-widest text-xs">Après-midi</h4>
              <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2 sm:gap-4 min-w-0">
                <input type="time" name="opening_time_afternoon" value={settings.opening_time_afternoon} onChange={handleChange} className={timeInputClass} />
                <span className="font-bold text-slate-400 text-center">à</span>
                <input type="time" name="closing_time_afternoon" value={settings.closing_time_afternoon} onChange={handleChange} className={timeInputClass} />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-[2rem] p-5 sm:p-8 border border-slate-100 shadow-sm space-y-8 min-w-0">
        <h3 className="text-xl font-bold flex items-center gap-3">
          <Calendar className="text-purple-500 shrink-0" />
          Mode d'Agenda
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 min-w-0">
          <label className={`min-w-0 border-2 p-5 sm:p-6 rounded-2xl cursor-pointer transition-all ${settings.agenda_mode === 'EXACT' ? 'border-primary bg-primary/5' : 'border-slate-100'}`}>
            <input type="radio" name="agenda_mode" value="EXACT" checked={settings.agenda_mode === 'EXACT'} onChange={handleChange} className="sr-only" />
            <h4 className="font-black text-lg mb-2">Mode Précis (Pointu)</h4>
            <p className="text-sm text-slate-500 font-medium">Créneaux horaires stricts (ex: 09:30, 10:00).</p>
          </label>
          <label className={`min-w-0 border-2 p-5 sm:p-6 rounded-2xl cursor-pointer transition-all ${settings.agenda_mode === 'BLOCK' ? 'border-primary bg-primary/5' : 'border-slate-100'}`}>
            <input type="radio" name="agenda_mode" value="BLOCK" checked={settings.agenda_mode === 'BLOCK'} onChange={handleChange} className="sr-only" />
            <h4 className="font-black text-lg mb-2">Mode Souple (Blocs)</h4>
            <p className="text-sm text-slate-500 font-medium">Les patients sont convoqués par demi-journée.</p>
          </label>
        </div>
      </div>

      <div className="bg-white rounded-[2rem] p-5 sm:p-8 border border-slate-100 shadow-sm space-y-8 min-w-0">
        <h3 className="text-xl font-bold flex items-center gap-3">
          <Ticket className="text-amber-500 shrink-0" />
          File d'attente (Tickets)
        </h3>

        <div className="flex items-start gap-4 min-w-0">
          <input
            type="checkbox"
            id="use_tickets"
            name="use_tickets"
            checked={settings.use_tickets}
            onChange={handleChange}
            className="w-6 h-6 shrink-0 rounded-xl border-slate-200 text-primary focus:ring-primary"
          />
          <div className="min-w-0">
            <label htmlFor="use_tickets" className="font-bold text-slate-700 block text-lg">Activer les tickets patients</label>
            <p className="text-slate-500 font-medium text-sm mt-1">Permet d'attribuer un numéro (1, 2, 3...) aux patients qui arrivent sans RDV.</p>
          </div>
        </div>
      </div>

      <div className="flex justify-stretch sm:justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full sm:w-auto bg-primary text-white font-black px-6 sm:px-12 py-4 rounded-2xl hover:bg-black transition-all shadow-xl shadow-primary/20"
        >
          {saving ? 'Sauvegarde...' : 'Sauvegarder Configuration'}
        </button>
      </div>
    </div>
  );
};
