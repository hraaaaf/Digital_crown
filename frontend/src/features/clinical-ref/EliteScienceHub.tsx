import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ExternalLink, ArrowLeft, GraduationCap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { scienceArticles } from '../../data/science_articles';
import { cn } from '../../utils/cn';

export const EliteScienceHub: React.FC = () => {
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState<string>('Tous');
  const [searchTerm, setSearchTerm] = useState('');

  const categories = ['Tous', 'ENDODONTIE', 'ORTHODONTIE', 'CHIRURGIE', 'PROTHESE', 'ESTHETIQUE', 'PARODONTOLOGIE'];

  const filteredArticles = scienceArticles.filter(art => {
    const matchesCategory = activeCategory === 'Tous' || art.category === activeCategory;
    const matchesSearch = art.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          art.authors.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-[#f8fafc] p-8 max-w-7xl mx-auto animate-in fade-in duration-700">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate(-1)}
            className="w-12 h-12 bg-white border border-slate-200 rounded-2xl flex items-center justify-center text-slate-400 hover:text-primary hover:border-primary transition-all shadow-sm"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <div className="flex items-center gap-2 mb-1">
               <GraduationCap size={16} className="text-primary" style={{ color: 'var(--primary)' }} />
               <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/60">Evidence-Based Dentistry</span>
            </div>
            <h1 className="text-3xl font-black text-slate-800 tracking-tight uppercase">Elite Science Hub</h1>
            <p className="text-slate-500 font-bold text-sm tracking-wide">Base de données de publications scientifiques de référence</p>
          </div>
        </div>

        {/* SEARCH */}
        <div className="relative w-full md:w-80">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            type="search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Rechercher un article..."
            className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-2xl text-sm font-bold text-slate-700 outline-none focus:ring-4 transition-all shadow-sm"
            style={{ ['--tw-ring-color' as string]: 'rgba(var(--primary-rgb), 0.08)' }}
          />
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
                ? "bg-slate-800 text-white border-slate-800 shadow-lg" 
                : "bg-white text-slate-400 border-slate-100 hover:border-slate-300"
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* ARTICLES GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <AnimatePresence mode="popLayout">
          {filteredArticles.map((article) => (
            <motion.div
              key={article.id}
              layout
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="group bg-white rounded-[2.5rem] border border-slate-100 p-8 shadow-sm hover:shadow-xl hover:border-primary/20 transition-all flex flex-col h-full"
            >
              <div className="flex justify-between items-start mb-6">
                <span className="text-[9px] font-black px-3 py-1 bg-primary/5 text-primary rounded-full uppercase tracking-widest" style={{ color: 'var(--primary)' }}>
                  {article.category}
                </span>
                <span className="text-[10px] font-bold text-slate-400">
                  {article.year}
                </span>
              </div>

              <h3 className="text-xl font-black text-slate-800 mb-4 leading-tight group-hover:text-primary transition-colors" style={{ color: 'var(--text-main)' }}>
                {article.title}
              </h3>
              
              <p className="text-sm font-bold text-slate-500 mb-6 italic">
                {article.authors} — <span className="text-slate-400">{article.journal}</span>
              </p>

              <div className="bg-slate-50 p-6 rounded-2xl mb-8 flex-1">
                <p className="text-sm leading-relaxed text-slate-600 font-medium">
                  {article.summary}
                </p>
              </div>

              <a 
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-4 bg-white border border-slate-200 rounded-2xl flex items-center justify-center gap-2 text-xs font-black uppercase tracking-widest hover:bg-slate-900 hover:text-white hover:border-slate-900 transition-all group/btn"
              >
                Consulter l'étude complète
                <ExternalLink size={14} className="group-hover/btn:translate-x-1 group-hover/btn:-translate-y-1 transition-transform" />
              </a>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {filteredArticles.length === 0 && (
        <div className="py-20 text-center">
          <p className="text-slate-400 font-bold">Aucun article ne correspond à votre recherche.</p>
        </div>
      )}
    </div>
  );
};
