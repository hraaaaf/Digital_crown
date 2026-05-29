import React, { useState } from 'react';
import { Plus, Trash2, Calendar, DollarSign, FileText, MessageCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface InstallmentStudioProps {
  patientId: string;
}

interface InstallmentItem {
  id: string;
  label: string;
  amount: number;
  dueDate: string;
  sendReminder?: boolean;
}

export const InstallmentStudio: React.FC<InstallmentStudioProps> = ({ patientId }) => {
  const [title, setTitle] = useState('Traitement Orthodontique');
  const [totalAmount, setTotalAmount] = useState<number>(0);
  const [advanceAmount, setAdvanceAmount] = useState<number>(0);
  const [advanceDate, setAdvanceDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [monthsCount, setMonthsCount] = useState<number>(1);
  const [monthlyAmount, setMonthlyAmount] = useState<number>(0);
  const [items, setItems] = useState<InstallmentItem[]>([]);

  const generateTable = () => {
    if (monthsCount < 1) {
      toast.error('Le nombre de mensualités doit être > 0');
      return;
    }
    const newItems: InstallmentItem[] = [];
    
    // Avance
    if (advanceAmount > 0) {
      newItems.push({
        id: 'advance',
        label: 'Avance Initiale',
        amount: advanceAmount,
        dueDate: advanceDate,
        sendReminder: false
      });
    }

    // Mensualités
    const currentDate = new Date(advanceDate);
    for (let i = 0; i < monthsCount; i++) {
      currentDate.setMonth(currentDate.getMonth() + 1);
      newItems.push({
        id: `inst_${i}`,
        label: `Mensualité ${i + 1}`,
        amount: monthlyAmount,
        dueDate: currentDate.toISOString().split('T')[0],
        sendReminder: false
      });
    }

    setItems(newItems);
  };

  const addItem = () => {
    setItems([...items, { id: `manual_${Date.now()}`, label: 'Nouveau versement', amount: 0, dueDate: new Date().toISOString().split('T')[0], sendReminder: false }]);
  };

  const updateItem = (id: string, field: keyof InstallmentItem, value: any) => {
    setItems(items.map(item => item.id === id ? { ...item, [field]: value } : item));
  };

  const removeItem = (id: string) => {
    setItems(items.filter(item => item.id !== id));
  };

  // Ce composant va exposer les données via un ref ou context si nécessaire pour useDocumentGenerator
  // Pour l'instant, DocumentHub s'attend à passer des données, mais useDocumentGenerator a peut-être besoin
  // d'être adapté pour extraire l'échéancier. On stocke l'état ici.
  
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 flex flex-col h-full overflow-y-auto" id="installment-studio-container" data-plan-data={JSON.stringify({title, totalAmount, items})}>
      <div className="mb-6">
        <h3 className="text-lg font-bold text-slate-900 mb-1">Configuration de l'Échéancier</h3>
        <p className="text-sm text-slate-500">Définissez le plan de paiement pour les traitements longs.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Titre du traitement</label>
          <div className="relative">
            <FileText className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input type="text" value={title} onChange={e => setTitle(e.target.value)} className="w-full pl-10 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" placeholder="Ex: Traitement Orthodontique" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Montant Total Prévu (MAD)</label>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input type="number" value={totalAmount} onChange={e => setTotalAmount(Number(e.target.value))} className="w-full pl-10 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
          </div>
        </div>
      </div>

      <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 mb-6">
        <h4 className="text-sm font-bold text-slate-800 mb-3">Génération Rapide</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Avance (MAD)</label>
            <input type="number" value={advanceAmount} onChange={e => setAdvanceAmount(Number(e.target.value))} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Date Avance</label>
            <input type="date" value={advanceDate} onChange={e => setAdvanceDate(e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Nbre Mensualités</label>
            <input type="number" min="1" value={monthsCount} onChange={e => setMonthsCount(Number(e.target.value))} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Montant / Mois (MAD)</label>
            <input type="number" value={monthlyAmount} onChange={e => setMonthlyAmount(Number(e.target.value))} className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" />
          </div>
        </div>
        <button onClick={generateTable} className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-sm font-medium rounded-lg transition-colors w-full">
          Générer le tableau des échéances
        </button>
      </div>

      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-bold text-slate-800">Échéances Prévues</h4>
        <button onClick={addItem} className="flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary hover:bg-primary/20 text-xs font-medium rounded-lg transition-colors">
          <Plus className="w-3.5 h-3.5" />
          Ajouter manuellement
        </button>
      </div>

      <div className="flex-1 overflow-y-auto min-h-[200px] border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-slate-500 bg-slate-50 border-b border-slate-200 uppercase">
            <tr>
              <th className="px-4 py-3 font-semibold">Libellé</th>
              <th className="px-4 py-3 font-semibold w-32">Date</th>
              <th className="px-4 py-3 font-semibold w-32">Montant</th>
              <th className="px-4 py-3 font-semibold w-32 text-center" title="Notification WhatsApp manuelle">Rappel WhatsApp</th>
              <th className="px-4 py-3 w-16"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-4 py-2">
                  <input type="text" value={item.label} onChange={(e) => updateItem(item.id, 'label', e.target.value)} className="w-full bg-transparent border-none focus:ring-0 p-0 text-sm font-medium text-slate-700" />
                </td>
                <td className="px-4 py-2">
                  <input type="date" value={item.dueDate} onChange={(e) => updateItem(item.id, 'dueDate', e.target.value)} className="w-full bg-transparent border-none focus:ring-0 p-0 text-sm text-slate-600" />
                </td>
                <td className="px-4 py-2">
                  <div className="flex items-center gap-1">
                    <input type="number" value={item.amount} onChange={(e) => updateItem(item.id, 'amount', Number(e.target.value))} className="w-full bg-transparent border-none focus:ring-0 p-0 text-sm font-bold text-slate-900" />
                    <span className="text-xs text-slate-400">MAD</span>
                  </div>
                </td>
                <td className="px-4 py-2 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <input 
                      type="checkbox" 
                      checked={item.sendReminder || false} 
                      onChange={(e) => updateItem(item.id, 'sendReminder', e.target.checked)}
                      className="w-4 h-4 text-emerald-500 rounded border-slate-300 focus:ring-emerald-500 cursor-pointer"
                    />
                    {item.sendReminder && (
                      <button 
                        onClick={() => {
                          const msg = `Bonjour, ceci est un rappel pour votre échéance: ${item.label} d'un montant de ${item.amount} MAD prévue le ${item.dueDate}. Merci.`;
                          window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`, '_blank');
                        }}
                        className="text-emerald-500 hover:text-emerald-600 transition-colors"
                        title="Envoyer le rappel maintenant"
                      >
                        <MessageCircle size={16} />
                      </button>
                    )}
                  </div>
                </td>
                <td className="px-4 py-2 text-right">
                  <button onClick={() => removeItem(item.id)} className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-500 text-sm">
                  Aucune échéance définie. Utilisez la génération rapide ou ajoutez manuellement.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center text-sm">
        <span className="text-slate-500">Total planifié : <b className="text-slate-900">{items.reduce((acc, it) => acc + (it.amount || 0), 0).toFixed(2)} MAD</b></span>
        {totalAmount > 0 && (
          <span className={items.reduce((acc, it) => acc + (it.amount || 0), 0) !== totalAmount ? "text-amber-500 font-medium" : "text-emerald-500 font-medium"}>
            {items.reduce((acc, it) => acc + (it.amount || 0), 0) === totalAmount ? "Total équilibré" : "Le total planifié diffère du total prévu"}
          </span>
        )}
      </div>
    </div>
  );
};
