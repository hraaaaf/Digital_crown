import { AlertTriangle, Loader2, Mail, Receipt, Search, Send } from 'lucide-react';
import { EliteGhostLoader } from '../../../components/EliteGhostLoader';
import { cn } from '../../../utils/cn';

interface TreasuryPanelProps {
  treasuryData: any;
  overdueData: any;
  loadingTreasury: boolean;
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  treasuryStatusFilter: string;
  setTreasuryStatusFilter: (value: string) => void;
  sendingEmail: string | null;
  handleRelance: (itemId: string) => void | Promise<void>;
  handlePatientClick: (patientId: number) => void;
  handleSendEmail: (itemId: string | number) => void | Promise<void>;
  handleViewDocument: (url: string) => void | Promise<void>;
  handleEncaisser: (id: string | number) => void | Promise<void>;
}

export const TreasuryPanel = ({
  treasuryData,
  overdueData,
  loadingTreasury,
  searchTerm,
  setSearchTerm,
  treasuryStatusFilter,
  setTreasuryStatusFilter,
  sendingEmail,
  handleRelance,
  handlePatientClick,
  handleSendEmail,
  handleViewDocument,
  handleEncaisser,
}: TreasuryPanelProps) => (
  <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
     {/* Treasury Overview Cards */}
     <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm flex flex-col gap-2">
           <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">En Attente</span>
           <span className="text-3xl font-black text-slate-800">{treasuryData?.pending_total?.toLocaleString('fr-FR')} MAD</span>
           <div className="flex items-center gap-2 text-amber-500 mt-2">
              <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              <span className="text-[10px] font-bold uppercase">{treasuryData?.pending_count} dossiers à régulariser</span>
           </div>
        </div>
        <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm flex flex-col gap-2">
           <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Règlements Partiels</span>
           <span className="text-3xl font-black text-slate-800">{treasuryData?.partial_total?.toLocaleString('fr-FR')} MAD</span>
           <span className="text-[10px] font-bold text-blue-500 uppercase mt-2 italic">Solde restant à percevoir</span>
        </div>
        <div className="bg-indigo-600 p-8 rounded-[2rem] shadow-xl shadow-indigo-200 flex flex-col gap-2 text-white">
           <span className="text-[10px] font-black text-indigo-200 uppercase tracking-widest">Alerte Chèques</span>
           <span className="text-3xl font-black">{treasuryData?.cheques_count || 0}</span>
           <p className="text-[10px] font-medium text-indigo-100 mt-2 leading-relaxed">
              Chèques en attente de dépôt bancaire ou d'encaissement définitif.
           </p>
        </div>
        <div className="bg-emerald-600 p-8 rounded-[2rem] shadow-xl shadow-emerald-200 flex flex-col gap-2 text-white">
           <span className="text-[10px] font-black text-emerald-200 uppercase tracking-widest">Potentiel Immédiat</span>
           <span className="text-3xl font-black">{( (treasuryData?.pending_total || 0) + (treasuryData?.partial_total || 0) ).toLocaleString('fr-FR')} MAD</span>
           <p className="text-[10px] font-medium text-emerald-100 mt-2 leading-relaxed">
              Trésorerie latente à recouvrir activement ce mois.
           </p>
        </div>
     </div>

     {/* OVERDUE ALERT BANNER */}
     {overdueData && overdueData.total > 0 && (
       <div className="bg-rose-50 border border-rose-200 rounded-[2rem] p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
         <div className="flex items-center gap-4">
           <div className="w-10 h-10 bg-rose-100 text-rose-600 rounded-xl flex items-center justify-center">
             <AlertTriangle size={20} />
           </div>
           <div>
             <p className="font-black text-rose-700 text-sm uppercase tracking-widest">
               {overdueData.total} note{overdueData.total > 1 ? 's' : ''} en retard &gt; 30 jours
             </p>
             <p className="text-[10px] text-rose-500 font-medium mt-0.5">
               Total : {overdueData.total_amount?.toLocaleString('fr-FR')} MAD non recouvré
             </p>
           </div>
         </div>
         <div className="flex flex-wrap gap-2">
           {overdueData.items.slice(0, 5).map((item: any) => (
             <div key={item.id} className="flex items-center gap-2 bg-white border border-rose-100 rounded-xl px-3 py-2">
               <div>
                 <p className="text-[10px] font-black text-slate-700">{item.patient_name}</p>
                 <p className="text-[9px] text-rose-400 font-bold">{item.amount.toLocaleString('fr-FR')} MAD — {item.days_overdue}j</p>
               </div>
               {item.patient_email && (
                 <button
                   onClick={() => handleRelance(item.id)}
                   disabled={sendingEmail === item.id}
                   className="p-1.5 bg-rose-50 text-rose-500 rounded-lg hover:bg-rose-500 hover:text-white transition-all border border-rose-100 disabled:opacity-50"
                   title="Envoyer relance email"
                 >
                   {sendingEmail === item.id ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
                 </button>
               )}
             </div>
           ))}
           {overdueData.total > 5 && (
             <span className="flex items-center px-3 py-2 text-[9px] font-black text-rose-400">+{overdueData.total - 5} autres</span>
           )}
         </div>
       </div>
     )}

     <div className="bg-white rounded-[2.5rem] border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-8 py-6 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
           <div>
             <h3 className="text-sm font-black text-slate-800 uppercase tracking-widest">Dossiers en souffrance</h3>
             <p className="text-[10px] text-slate-400 font-medium">Liste des notes non réglées ou partiellement réglées</p>
           </div>

           <div className="flex flex-wrap items-center gap-3">
              <div className="relative group">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-600 transition-colors" size={14} />
                <input 
                  type="text" 
                  placeholder="Rechercher..." 
                  className="pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-[10px] font-bold focus:ring-4 focus:ring-indigo-500/5 outline-none transition-all w-48"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <select
                className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-[10px] font-bold outline-none focus:ring-4 focus:ring-indigo-500/5"
                value={treasuryStatusFilter}
                onChange={(e) => setTreasuryStatusFilter(e.target.value)}
              >
                <option value="ALL">Tous Statuts</option>
                <option value="EN_ATTENTE">En Attente</option>
                <option value="PARTIEL">Partiel</option>
              </select>
           </div>
        </div>

       {loadingTreasury ? (
         <div className="py-10 relative h-[300px]">
           <EliteGhostLoader text="Chargement..." fullScreen={false} size="small" />
         </div>
       ) : (
         <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-100">
                <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest">Patient</th>
                <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest">Date Émission</th>
                <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest">Montant</th>
                <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest">Statut</th>
                <th className="px-8 py-4 text-[9px] font-black text-slate-400 uppercase tracking-widest text-center">Action</th>
              </tr>
            </thead>
            <tbody>
              {(treasuryData?.items || [])
                .filter((item: any) =>
                  (item.patient_name.toLowerCase().includes(searchTerm.toLowerCase())) &&
                  (treasuryStatusFilter === 'ALL' || item.status === treasuryStatusFilter)
                )
                .map((item: any) => (
                <tr key={item.id} className="border-b border-slate-100 hover:bg-slate-50 transition-all group">
                  <td className="px-8 py-5">
                    <button 
                      onClick={() => handlePatientClick(item.patient_id)}
                      className="font-bold text-slate-700 hover:text-indigo-600 transition-colors text-left"
                    >
                      {item.patient_name}
                    </button>
                  </td>
                  <td className="px-8 py-5 text-sm text-slate-500">
                    {new Date(item.date).toLocaleDateString('fr-FR')}
                  </td>
                  <td className="px-8 py-5">
                    <span className="font-black text-indigo-600">{item.amount.toLocaleString('fr-FR')} MAD</span>
                  </td>
                  <td className="px-8 py-5">
                    <span className={cn(
                      "px-2.5 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest",
                      item.status === 'EN_ATTENTE' ? "bg-amber-100 text-amber-700" : 
                      item.status === 'A_ENCAISSER' ? "bg-blue-100 text-blue-700" :
                      "bg-purple-100 text-purple-700"
                    )}>
                      {item.status === 'EN_ATTENTE' ? 'En Attente' : 
                       item.status === 'A_ENCAISSER' ? 'À Encaisser' : 'Partiel'}
                    </span>
                  </td>
                  <td className="px-8 py-5">
                    <div className="flex justify-center gap-2">
                       <button
                          onClick={() => handleSendEmail(`doc_${item.id}`)}
                          disabled={sendingEmail === `doc_${item.id}`}
                          className="p-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-600 hover:text-white transition-all border border-blue-100 disabled:opacity-50"
                          title="Envoyer par email"
                       >
                          {sendingEmail === `doc_${item.id}` ? <Loader2 size={14} className="animate-spin" /> : <Mail size={14} />}
                       </button>
                       <button
                          onClick={() => handleViewDocument(`documents/${item.id}/download`)}
                          className="p-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-600 hover:text-white transition-all border border-indigo-100"
                          title="Voir la note"
                       >
                          <Receipt size={14} />
                       </button>
                       <button
                          onClick={() => handleEncaisser(item.id)}
                          className="px-4 py-2 bg-emerald-50 text-emerald-600 rounded-xl text-[9px] font-black uppercase tracking-widest border border-emerald-100 hover:bg-emerald-600 hover:text-white transition-all"
                       >
                          Encaisser
                       </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
         </table>
       )}
     </div>
   </div>
);
