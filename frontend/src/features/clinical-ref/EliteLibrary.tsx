import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Star, Search, Clock, ChevronRight, X, Brain } from 'lucide-react';
import { CLINICAL_PROTOCOLS } from '../../data/clinical-protocols';
import type { ClinicalProtocol } from './types';
import { cn } from '../../utils/cn';
import { ClinicalRefContent } from './ClinicalRefContent';

export const EliteLibrary: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<string>('Tous');
  const [showOnlyFavorites, setShowOnlyFavorites] = useState(false);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [selectedProtocol, setSelectedProtocol] = useState<ClinicalProtocol | null>(null);

  // Load favorites from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('elite_library_favorites');
    if (saved) {
      setFavorites(JSON.parse(saved));
    }
  }, []);

  const toggleFavorite = (e: React.MouseEvent, code: string) => {
    e.stopPropagation();
    const newFavs = favorites.includes(code)
      ? favorites.filter(f => f !== code)
      : [...favorites, code];
    
    setFavorites(newFavs);
    localStorage.setItem('elite_library_favorites', JSON.stringify(newFavs));
  };

  const categories = ['Tous', 'CHIRURGIE', 'ENDODONTIE', 'IMPLANTOLOGIE', 'PARODONTOLOGIE', 'CONSERVATRICE', 'PROTHESE', 'ORTHODONTIE', 'ESTHETIQUE', 'PREVENTION', 'PEDIATRIE'];

  const getCategory = (code: string): string => {
    // CHIRURGIE
    if (code.includes('extraction') || code.includes('avulsion') || code.includes('alveo') ||
        code.includes('germecto') || code.includes('apicecto') || code.includes('frenecto'))
      return 'CHIRURGIE';
    // ENDODONTIE
    if (code.includes('endo') || code.includes('canalaire') || code.includes('retraitement') ||
        code.includes('pulpotomie') || code.includes('pulpo') || code.includes('coiffage'))
      return 'ENDODONTIE';
    // IMPLANTOLOGIE
    if (code.includes('implant') || code.includes('sinus') || code.includes('greffe-osseus') ||
        code.includes('greffe-osseuse') || code.includes('couronne-sur-implant'))
      return 'IMPLANTOLOGIE';
    // PARODONTOLOGIE
    if (code.includes('detartrage') || code.includes('surfacage') || code.includes('gingivecto') ||
        code.includes('greffe-gingivale') || code.includes('lambeau') || code.includes('widman'))
      return 'PARODONTOLOGIE';
    // CONSERVATRICE
    if (code.includes('scellement') || code.includes('composite') || code.includes('reconstitution') ||
        code.includes('inlay') || code.includes('onlay') || code.includes('dentine') || code.includes('tenon'))
      return 'CONSERVATRICE';
    // PROTHESE
    if (code.includes('couronne-ceramique') || code.includes('couronne-zircone') || code.includes('bridge') ||
        code.includes('prothese') || code.includes('preparation-couronne'))
      return 'PROTHESE';
    // ORTHODONTIE
    if (code.includes('ortho') || code.includes('collage-ortho') || code.includes('aligneur') || code.includes('bilan-ortho'))
      return 'ORTHODONTIE';
    // ESTHETIQUE
    if (code.includes('bleach') || code.includes('blanchiment') || code.includes('facette'))
      return 'ESTHETIQUE';
    // PREVENTION
    if (code.includes('examen') || code.includes('vernis') || code.includes('radio') || code.includes('cbct'))
      return 'PREVENTION';
    // PEDIATRIE
    if (code.includes('pedod') || code.includes('pediatr') || code.includes('lacteale') || code.includes('lactal'))
      return 'PEDIATRIE';
    return '';
  };

  const filteredProtocols = CLINICAL_PROTOCOLS.filter(p => {
    const category = getCategory(p.act_code.toLowerCase());
    const matchesCategory = activeCategory === 'Tous' || category === activeCategory;
    const matchesFav = !showOnlyFavorites || favorites.includes(p.act_code);
    return matchesCategory && matchesFav;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto animate-in fade-in duration-700">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center text-primary" style={{ color: 'var(--primary)' }}>
            <BookOpen size={28} />
          </div>
          <div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight uppercase">Bibliothèque Elite</h1>
            <p className="text-slate-400 font-bold text-sm tracking-wide">Protocoles cliniques certifiés (Statiques)</p>
          </div>
        </div>

        <div className="flex items-center gap-3 bg-white/50 backdrop-blur-xl p-1.5 rounded-2xl border border-slate-200/60 shadow-sm">
          <button
            onClick={() => setShowOnlyFavorites(false)}
            className={cn(
              "px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all",
              !showOnlyFavorites ? "bg-white shadow-md text-primary" : "text-slate-400 hover:text-slate-600"
            )}
            style={!showOnlyFavorites ? { color: 'var(--primary)' } : {}}
          >
            Tous
          </button>
          <button
            onClick={() => setShowOnlyFavorites(true)}
            className={cn(
              "px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2",
              showOnlyFavorites ? "bg-white shadow-md text-primary" : "text-slate-400 hover:text-slate-600"
            )}
            style={showOnlyFavorites ? { color: 'var(--primary)' } : {}}
          >
            <Star size={14} className={cn(showOnlyFavorites && "fill-current")} />
            Favoris
          </button>
        </div>
      </div>

      {/* CATEGORIES */}
      <div className="flex flex-wrap gap-2 mb-10">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={cn(
              "px-5 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] border transition-all",
              activeCategory === cat 
                ? "bg-slate-800 text-white border-slate-800 shadow-lg shadow-slate-200" 
                : "bg-white text-slate-400 border-slate-100 hover:border-slate-300"
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <AnimatePresence mode="popLayout">
          {filteredProtocols.map((protocol) => (
            <motion.div
              key={protocol.act_code}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              whileHover={{ y: -8 }}
              onClick={() => setSelectedProtocol(protocol)}
              className="group bg-white/60 backdrop-blur-xl rounded-[2.5rem] border border-white/80 p-8 shadow-[0_8px_40px_-12px_rgba(0,0,0,0.05)] hover:shadow-[0_20px_60px_-15px_rgba(0,0,0,0.1)] hover:bg-white transition-all cursor-pointer relative overflow-hidden"
            >
              {/* Difficulte Badge */}
              <div className="flex justify-between items-start mb-6">
                <span className={cn(
                   "text-[9px] font-black px-2.5 py-1 rounded-lg uppercase tracking-widest",
                   protocol.difficulty === 'complex' ? "bg-orange-50 text-orange-600" : 
                   protocol.difficulty === 'specialist' ? "bg-red-50 text-red-600" : "bg-emerald-50 text-emerald-600"
                 )}>
                   {protocol.difficulty}
                 </span>
                 <button 
                  onClick={(e) => toggleFavorite(e, protocol.act_code)}
                  className={cn(
                    "p-2 rounded-xl transition-all",
                    favorites.includes(protocol.act_code) ? "text-amber-500 bg-amber-50" : "text-slate-200 hover:text-amber-500 hover:bg-amber-50"
                  )}
                 >
                   <Star size={20} fill={favorites.includes(protocol.act_code) ? "currentColor" : "none"} />
                 </button>
              </div>

              <h3 className="text-xl font-black text-slate-800 mb-2 leading-tight uppercase tracking-tight group-hover:text-primary transition-colors" style={{ color: 'var(--text-main)' }}>
                {protocol.act_names[0]}
              </h3>
              
              <div className="flex items-center gap-4 text-slate-400 text-xs font-bold mb-8">
                <div className="flex items-center gap-1.5">
                  <Clock size={14} />
                  <span>~{protocol.duration_min} min</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Brain size={14} className="text-primary" style={{ color: 'var(--primary)' }} />
                  <span>{protocol.checklist.length} points</span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-6 border-t border-slate-100">
                <span className="text-[10px] font-black text-primary uppercase tracking-widest" style={{ color: 'var(--primary)' }}>Ouvrir le guide</span>
                <div className="w-10 h-10 bg-slate-50 rounded-full flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-all shadow-sm">
                  <ChevronRight size={20} />
                </div>
              </div>

              <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-all" />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* EMPTY STATE */}
      {filteredProtocols.length === 0 && (
        <div className="py-20 text-center">
          <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center text-slate-300 mx-auto mb-6">
            <Search size={40} />
          </div>
          <h3 className="text-xl font-black text-slate-800 mb-2">Aucun protocole trouvé</h3>
          <p className="text-slate-400 font-bold">Essayez de changer les filtres ou de désactiver les favoris.</p>
        </div>
      )}

      {/* MODAL VIEW */}
      <AnimatePresence>
        {selectedProtocol && (
          <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4 md:p-8">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedProtocol(null)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" 
            />
            
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="bg-white rounded-[3rem] shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden relative z-10 flex flex-col border border-white"
            >
              <div className="p-8 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary" style={{ color: 'var(--primary)' }}>
                    <Brain size={24} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-black text-slate-800 uppercase tracking-tight">{selectedProtocol.act_names[0]}</h2>
                    <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">{selectedProtocol.difficulty} • ~{selectedProtocol.duration_min} minutes</p>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedProtocol(null)}
                  className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center text-slate-400 hover:text-rose-500 hover:shadow-lg transition-all"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-10 custom-scrollbar">
                <ClinicalRefContent protocol={selectedProtocol} />
              </div>
              
              <div className="p-8 border-t border-slate-50 bg-slate-50/30 flex justify-end">
                <button 
                  onClick={() => setSelectedProtocol(null)}
                  className="px-8 py-3 bg-slate-900 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-primary transition-all"
                >
                  Fermer le guide
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
