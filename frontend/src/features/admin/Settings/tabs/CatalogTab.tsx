import React, { useEffect, useState } from 'react';
import { useCatalogStore } from '../hooks/useCatalogStore';
import { Plus, FolderPlus, Activity, Stethoscope, Pencil } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import { SettingsReadError } from '../components/SharedUI';

export const CatalogTab: React.FC = () => {
  const { specialties, loading, readError, fetchCatalog, createSpecialty, createPathology, createAct, updateAct } = useCatalogStore();
  const [activeSpecialtyId, setActiveSpecialtyId] = useState<number | null>(null);

  useEffect(() => { void fetchCatalog(); }, [fetchCatalog]);

  const handleAddSpecialty = () => {
    const name = prompt('Nom de la spécialité (ex: Orthodontie) :');
    if (name) void createSpecialty({ name, color: '#3B82F6' });
  };
  const handleAddPathology = (specialtyId: number) => {
    const name = prompt('Nom de la pathologie :');
    if (name) void createPathology(specialtyId, { name });
  };
  const handleAddAct = (specialtyId: number) => {
    const name = prompt("Nom de l'acte :");
    if (!name) return;
    const priceStr = prompt('Prix de base (DHS) :');
    const price = parseFloat(priceStr || '0');
    void createAct(specialtyId, { name, base_price: price });
  };

  const handleEditPrice = (act: { id: number; name: string; base_price: number }) => {
    const priceStr = prompt(`Nouveau tarif pour « ${act.name} » (DHS) :`, String(act.base_price));
    if (priceStr === null) return;
    const price = parseFloat(priceStr.replace(',', '.'));
    if (isNaN(price) || price < 0 || price === act.base_price) return;
    void updateAct(act.id, { base_price: price });
  };

  if (loading && specialties.length === 0) {
    return <div className="p-8 text-center text-slate-500 animate-pulse font-bold tracking-widest uppercase text-sm">Chargement du catalogue...</div>;
  }
  if (readError) return <SettingsReadError title="Catalogue indisponible" message={readError} onRetry={fetchCatalog} />;

  const activeSpecialty = specialties.find(s => s.id === activeSpecialtyId) || specialties[0];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-black text-slate-900 tracking-tight">Catalogue Dynamique</h2>
          <p className="text-sm font-medium text-slate-500 mt-1">Gérez vos spécialités, actes et pathologies pour tous les modules.</p>
        </div>
        <button onClick={handleAddSpecialty} className="bg-slate-900 text-white px-5 py-3 rounded-2xl font-bold flex items-center gap-2 hover:bg-black transition-all shadow-xl shadow-slate-900/20">
          <Plus size={18} /> Nouvelle Spécialité
        </button>
      </div>

      <div className="flex flex-col xl:flex-row gap-8">
        <div className="w-full xl:w-1/3 flex flex-col gap-3">
          {specialties.map(spec => (
            <button key={spec.id} onClick={() => setActiveSpecialtyId(spec.id)} className={cn("w-full text-left p-5 rounded-[1.5rem] border transition-all duration-300 group flex items-center justify-between", (activeSpecialty?.id === spec.id) ? "bg-slate-900 text-white border-slate-900 shadow-2xl shadow-slate-900/20" : "bg-white border-slate-100 hover:border-slate-300 hover:shadow-lg text-slate-700")}>
              <div className="flex items-center gap-4">
                <div className={cn("p-3 rounded-2xl transition-colors", (activeSpecialty?.id === spec.id) ? "bg-white/10" : "bg-slate-50 group-hover:bg-slate-100")}>
                  <Stethoscope size={22} className={(activeSpecialty?.id === spec.id) ? "text-white" : "text-slate-600"} />
                </div>
                <div>
                  <h3 className="font-bold text-[1.1rem] tracking-tight">{spec.name}</h3>
                  <p className={cn("text-xs font-semibold mt-1", (activeSpecialty?.id === spec.id) ? "text-slate-400" : "text-slate-500")}>{spec.acts.length} actes • {spec.pathologies.length} pathol.</p>
                </div>
              </div>
            </button>
          ))}
          {specialties.length === 0 && (
            <div className="p-12 text-center border-2 border-dashed border-slate-200 rounded-[2rem] text-slate-400 bg-slate-50/50">
              <p className="font-bold text-lg text-slate-500 mb-2">Aucune spécialité</p>
              <p className="text-sm">Commencez par ajouter une spécialité pour construire votre catalogue.</p>
            </div>
          )}
        </div>

        {activeSpecialty && (
          <div className="flex-1 space-y-6">
            <div className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-xl shadow-slate-100/50 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/5 rounded-full blur-3xl pointer-events-none -translate-y-1/2 translate-x-1/3" />
              <div className="flex justify-between items-center mb-6 relative">
                <h3 className="text-xl font-black text-slate-900 flex items-center gap-3">
                  <div className="p-2 bg-sky-100 text-sky-600 rounded-xl"><Activity size={20} /></div>
                  Actes Cliniques
                </h3>
                <button onClick={() => handleAddAct(activeSpecialty.id)} className="bg-sky-50 text-sky-600 px-4 py-2 rounded-xl font-bold hover:bg-sky-100 transition-colors text-sm flex items-center gap-2"><Plus size={16} /> Ajouter</button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 relative">
                {activeSpecialty.acts.map(act => (
                  <div key={act.id} className="bg-white p-5 rounded-[1.25rem] shadow-sm border border-slate-100 flex justify-between items-center hover:border-sky-200 transition-colors group">
                    <div>
                      <p className="font-bold text-slate-700 group-hover:text-slate-900">{act.name}</p>
                      {act.code && <p className="text-[10px] text-slate-400 font-mono mt-1 font-bold bg-slate-50 inline-block px-1.5 py-0.5 rounded">{act.code}</p>}
                    </div>
                    <button onClick={() => handleEditPrice(act)} title="Modifier le tarif" className="font-black text-sky-700 bg-sky-50 px-3 py-1.5 rounded-xl text-sm flex items-center gap-1.5 hover:bg-sky-100 hover:ring-2 hover:ring-sky-200 transition-all cursor-pointer">
                      {act.base_price} DHS <Pencil size={12} className="opacity-0 group-hover:opacity-60 transition-opacity" />
                    </button>
                  </div>
                ))}
                {activeSpecialty.acts.length === 0 && <div className="col-span-full py-8 text-center text-slate-400 text-sm font-medium">Aucun acte dans cette spécialité</div>}
              </div>
            </div>

            <div className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-xl shadow-slate-100/50 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-rose-500/5 rounded-full blur-3xl pointer-events-none -translate-y-1/2 translate-x-1/3" />
              <div className="flex justify-between items-center mb-6 relative">
                <h3 className="text-xl font-black text-slate-900 flex items-center gap-3">
                  <div className="p-2 bg-rose-100 text-rose-600 rounded-xl"><FolderPlus size={20} /></div>
                  Pathologies
                </h3>
                <button onClick={() => handleAddPathology(activeSpecialty.id)} className="bg-rose-50 text-rose-600 px-4 py-2 rounded-xl font-bold hover:bg-rose-100 transition-colors text-sm flex items-center gap-2"><Plus size={16} /> Ajouter</button>
              </div>
              <div className="flex flex-wrap gap-2 relative">
                {activeSpecialty.pathologies.map(path => <div key={path.id} className="bg-white border border-slate-200 text-slate-600 px-4 py-2.5 rounded-xl shadow-sm font-bold text-sm hover:border-rose-200 hover:text-rose-600 transition-colors cursor-default">{path.name}</div>)}
                {activeSpecialty.pathologies.length === 0 && <div className="w-full py-8 text-center text-slate-400 text-sm font-medium">Aucune pathologie dans cette spécialité</div>}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
