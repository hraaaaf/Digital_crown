import React, { useState, useEffect, useRef } from 'react';
import { Camera, Printer, Clock, FileText, CheckCircle2, Bot, User, Send, ChevronRight, Zap } from 'lucide-react';
import { useOrthoStore } from '../stores/useOrthoStore';

interface Step4DocumentsProps {
  P: any;
}

interface ChatMessage {
  id: number;
  text: string;
  sender: 'bot' | 'user';
  isTyping?: boolean;
}

export const Step4Documents: React.FC<Step4DocumentsProps> = ({ P }) => {
  const store = useOrthoStore();
  const { 
    photos, 
    handlePhotoUpload: onUpload, 
    handlePrint: onGeneratePDF, 
    handlePreview: onPreviewPDF, 
    isPrinting: isGenerating,
    etape3Data,
    patientName
  } = store;

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatState, setChatState] = useState<'init' | 'typing' | 'ask_appliance' | 'ask_ortho_technique' | 'ask_torque' | 'ask_extractions' | 'done'>('init');
  const [options, setOptions] = useState<string[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const isChild = etape3Data.denture_type !== 'PERMANENTE' || (etape3Data.age !== '' && Number(etape3Data.age) < 12);
  const isSevereDDM = etape3Data.severite_ddm === 'sévère';

  const addBotMessage = (text: string, delay: number = 800) => {
    return new Promise<void>(resolve => {
      setChatMessages(prev => [...prev, { id: Date.now(), text: '', sender: 'bot', isTyping: true }]);
      setTimeout(() => {
        setChatMessages(prev => prev.map(m => m.isTyping ? { ...m, text, isTyping: false } : m));
        resolve();
      }, delay);
    });
  };

  const addUserMessage = (text: string) => {
    setChatMessages(prev => [...prev, { id: Date.now(), text, sender: 'user' }]);
    setOptions([]); // hide options
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, options]);

  // Initialisation de la discussion
  useEffect(() => {
    if (chatState !== 'init') return;
    
    const startConversation = async () => {
      setChatState('typing');
      await addBotMessage(`Bonjour Docteur. J'ai analysé les données de ${patientName || 'ce patient'}.`, 600);
      
      if (isChild) {
        await addBotMessage(`Le patient est en phase de croissance (denture ${etape3Data.denture_type?.toLowerCase() || 'mixte'}). Une phase d'orthopédie est requise en première intention.`, 1200);
        await addBotMessage(`Face à ce tableau clinique (Classe ${etape3Data.classe_squelettique || 'I'}, DDM ${etape3Data.severite_ddm || 'Légère'}), quel est votre appareil orthopédique de prédilection ?`, 1500);
        setOptions(['D-Gainer', 'Perle de Tuca', 'QuadHelix', 'Disjoncteur', 'Activateur', 'Fronde']);
        setChatState('ask_appliance');
      } else {
        await addBotMessage(`Le patient est en denture permanente. La stratégie s'oriente vers un traitement orthodontique global.`, 1200);
        
        if (isSevereDDM) {
          await addBotMessage(`⚠️ Une DDM SÉVÈRE est détectée. Le plan d'extraction est souvent requis dans cette configuration.`, 1000);
          await addBotMessage(`Validez-vous un traitement avec extractions (ex: 14, 24) ?`, 800);
          setOptions(['Avec Extractions', 'Sans Extractions']);
          setChatState('ask_extractions');
        } else {
          await addBotMessage(`Quelle technique orthodontique privilégiez-vous pour ce cas ?`, 1000);
          setOptions(['Damon (Autoligaturant)', 'Multi-attaches Classique', 'Aligneurs (Invisalign)']);
          setChatState('ask_ortho_technique');
        }
      }
    };

    startConversation();
  }, [chatState, isChild, isSevereDDM, etape3Data, patientName]);

  const handleOptionClick = async (opt: string) => {
    addUserMessage(opt);
    setChatState('typing');

    if (chatState === 'ask_appliance') {
      await addBotMessage(`Excellent choix, le ${opt} sera parfaitement adapté. Note mémorisée.`, 800);
      await addBotMessage(`Voulez-vous associer à de l'orthodontie préceptive (technique 2x4) ou attendre la denture permanente pour la phase 2 ?`, 1200);
      setOptions(['Associer orthodontie (2x4)', 'Attendre denture permanente']);
      setChatState('ask_ortho_technique'); // Reusing state for simplicity
    } 
    else if (chatState === 'ask_extractions') {
      await addBotMessage(`C'est noté pour le choix : ${opt}.`, 800);
      await addBotMessage(`Quelle technique orthodontique privilégiez-vous pour aligner ?`, 1000);
      setOptions(['Damon (Autoligaturant)', 'Multi-attaches Classique', 'Aligneurs (Invisalign)']);
      setChatState('ask_ortho_technique');
    }
    else if (chatState === 'ask_ortho_technique') {
      if (opt.includes('Damon')) {
        await addBotMessage(`Technique Damon sélectionnée.`, 600);
        await addBotMessage(`Pour optimiser la mécanique Damon, quel choix de torque préconisez-vous au maxillaire ? (Le profil du patient est ${etape3Data.profil || 'inconnu'})`, 1500);
        setOptions(['High Torque', 'Standard Torque', 'Low Torque']);
        setChatState('ask_torque');
      } else {
        finishConversation();
      }
    }
    else if (chatState === 'ask_torque') {
      await addBotMessage(`Torque ${opt.replace(' Torque', '')} sélectionné. Le plan mécanique est validé.`, 1000);
      finishConversation();
    }
  };

  const finishConversation = async () => {
    setChatState('typing');
    await addBotMessage(`Le plan de traitement est désormais verrouillé. Vous pouvez générer le bilan céphalométrique complet (PDF) pour l'archiver dans le dossier du patient.`, 1500);
    setChatState('done');
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 max-h-[85vh] overflow-hidden flex flex-col">
      
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-full">
        
        {/* COLONNE GAUCHE : PHOTOS (Span 5) */}
        <div className="lg:col-span-5 flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar" style={{ maxHeight: '75vh' }}>
          <h3 className="text-sm font-black uppercase tracking-widest mb-2" style={{ color: P.text }}>Dossier Photographique</h3>
          <div className="grid grid-cols-2 gap-3">
            {photos.map((photo) => (
              <div 
                key={photo.id}
                className="group relative aspect-square rounded-2xl overflow-hidden border-2 border-dashed transition-all hover:border-solid"
                style={{ 
                  background: P.bgCard, 
                  borderColor: photo.preview ? P.accentSuccess : P.border,
                  borderStyle: photo.preview ? 'solid' : 'dashed'
                }}
              >
                {photo.preview ? (
                  <>
                    <img src={photo.preview} alt={photo.label} className="w-full h-full object-cover transition-transform group-hover:scale-105" />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                      <label className="cursor-pointer p-2 bg-white/20 backdrop-blur-md rounded-full text-white hover:bg-white/40">
                        <Camera size={20} />
                        <input type="file" className="hidden" accept="image/*" onChange={(e) => e.target.files?.[0] && onUpload(photo.id, e.target.files[0])} />
                      </label>
                    </div>
                    <div className="absolute top-2 right-2 p-1 bg-emerald-500 rounded-full text-white shadow-lg">
                      <CheckCircle2 size={12} />
                    </div>
                  </>
                ) : (
                  <label className="flex flex-col items-center justify-center w-full h-full cursor-pointer p-4 text-center gap-3">
                    <Camera size={24} style={{ color: P.textDim }} />
                    <span className="text-[9px] font-black uppercase tracking-widest leading-tight" style={{ color: P.textMuted }}>{photo.label}</span>
                    <input type="file" className="hidden" accept="image/*" onChange={(e) => e.target.files?.[0] && onUpload(photo.id, e.target.files[0])} />
                  </label>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* COLONNE DROITE : GHOST BRAIN CHAT (Span 7) */}
        <div className="lg:col-span-7 flex flex-col h-[75vh] rounded-[2rem] overflow-hidden border shadow-xl relative" style={{ background: P.bgPanel, borderColor: P.border }}>
          
          {/* Header du Chat */}
          <div className="px-6 py-4 border-b flex items-center justify-between bg-white/50 backdrop-blur-md z-10" style={{ borderColor: P.border }}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
                <Bot size={20} />
              </div>
              <div>
                <h3 className="text-sm font-black uppercase tracking-widest text-slate-800 flex items-center gap-2">
                  Ghost Brain ODF <span className="bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded-full text-[8px]">v4.0</span>
                </h3>
                <p className="text-[10px] font-bold text-slate-400">Assistant Clinique IA</p>
              </div>
            </div>
            {chatState === 'done' && (
              <div className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-[9px] font-black uppercase tracking-widest flex items-center gap-1 border border-emerald-200">
                <CheckCircle2 size={12} /> Plan Validé
              </div>
            )}
          </div>

          {/* Zone des messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar bg-slate-50/50">
            {chatMessages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2`}>
                <div className={`max-w-[80%] p-4 rounded-[1.5rem] ${
                  msg.sender === 'user' 
                    ? 'bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-500/20' 
                    : 'bg-white text-slate-700 rounded-bl-none shadow-sm border border-slate-100'
                }`}>
                  {msg.isTyping ? (
                    <div className="flex items-center gap-1.5 px-2 py-1">
                      <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  ) : (
                    <p className="text-sm font-medium leading-relaxed">{msg.text}</p>
                  )}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Zone des réponses (Options ou Boutons Finaux) */}
          <div className="p-4 bg-white border-t" style={{ borderColor: P.border }}>
            {options.length > 0 && (
              <div className="flex flex-wrap gap-2 justify-end animate-in fade-in slide-in-from-bottom-2">
                {options.map((opt) => (
                  <button
                    key={opt}
                    onClick={() => handleOptionClick(opt)}
                    className="px-4 py-2 bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-600 hover:text-white transition-all rounded-full text-xs font-bold shadow-sm"
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}
            
            {chatState === 'done' && (
              <div className="flex flex-col gap-3 animate-in fade-in zoom-in duration-500">
                <div className="text-[10px] font-black text-center text-slate-400 uppercase tracking-widest mb-1">
                  ACTIONS DISPONIBLES
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={onPreviewPDF}
                    disabled={isGenerating}
                    className="w-full px-6 py-4 rounded-2xl font-black uppercase tracking-widest transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2 bg-white text-slate-700 border border-slate-200 hover:border-slate-300 shadow-sm"
                  >
                    <FileText size={18} /> Aperçu
                  </button>
                  <button 
                    onClick={onGeneratePDF}
                    disabled={isGenerating}
                    className="w-full px-6 py-4 rounded-2xl font-black uppercase tracking-widest text-white shadow-xl shadow-indigo-500/20 flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 bg-gradient-to-r from-indigo-600 to-purple-600"
                  >
                    {isGenerating ? <Clock size={18} className="animate-spin" /> : <Printer size={18} />}
                    Générer Bilan
                  </button>
                </div>
              </div>
            )}
            
            {chatState !== 'done' && options.length === 0 && chatState !== 'typing' && (
              <div className="h-14 flex items-center justify-center text-[10px] font-black text-slate-300 uppercase tracking-widest">
                En attente de réponse...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
