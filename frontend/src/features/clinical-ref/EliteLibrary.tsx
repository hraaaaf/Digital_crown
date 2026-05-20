import React, { useState, useEffect, useMemo, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { CLINICAL_PROTOCOLS } from '../../data/clinical-protocols';

import { ClinicalRefContent } from './ClinicalRefContent';
import { ClinicalSoinMode } from './ClinicalSoinMode';
import { cn } from '../../utils/cn';

const DIFF_FR = { routine: "Courant", complex: "Complexe", specialist: "Spécialiste" };
const DIFF_DOTS = { routine: 1, complex: 2, specialist: 3 };

export const EliteLibrary: React.FC = () => {
  const navigate = useNavigate();
  const { code: routeCode } = useParams<{ code?: string }>();
  
  const [activeCategory, setActiveCategory] = useState<string>('Tous');
  const [favorites, setFavorites] = useState<string[]>([]);
  const [recents, setRecents] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sort, setSort] = useState<'alpha' | 'difficulty' | 'category'>('alpha');
  const [view, setView] = useState<'grid' | 'list'>('grid');
  
  const [openProtocolCode, setOpenProtocolCode] = useState<string | null>(routeCode || null);
  const [showCmd, setShowCmd] = useState(false);
  const [cmdSearch, setCmdSearch] = useState('');
  const [soinModeCode, setSoinModeCode] = useState<string | null>(null);
  
  const cmdInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setOpenProtocolCode(routeCode || null);
  }, [routeCode]);

  useEffect(() => {
    const savedFavs = localStorage.getItem('dc_favs');
    if (savedFavs) setFavorites(JSON.parse(savedFavs));
    
    const savedRecents = localStorage.getItem('dc_recents');
    if (savedRecents) setRecents(JSON.parse(savedRecents));
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setShowCmd(true);
      }
      if (e.key === 'Escape') {
        if (showCmd) setShowCmd(false);
        else if (openProtocolCode) closePanel();
      }
      if (openProtocolCode && e.key === 'ArrowRight') { navProtocol(1); }
      if (openProtocolCode && e.key === 'ArrowLeft') { navProtocol(-1); }
      if (openProtocolCode && e.key.toLowerCase() === 'p' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT') {
        window.print();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  useEffect(() => {
    if (showCmd && cmdInputRef.current) {
      cmdInputRef.current.focus();
    }
  }, [showCmd]);

  const persistFavs = (favs: string[]) => {
    setFavorites(favs);
    localStorage.setItem('dc_favs', JSON.stringify(favs));
  };

  const persistRecents = (recs: string[]) => {
    setRecents(recs);
    localStorage.setItem('dc_recents', JSON.stringify(recs));
  };

  const toggleFav = (e: React.MouseEvent, code: string) => {
    e.stopPropagation();
    const newFavs = favorites.includes(code)
      ? favorites.filter(f => f !== code)
      : [...favorites, code];
    persistFavs(newFavs);
  };

  const openPanel = (code: string) => {
    const p = CLINICAL_PROTOCOLS.find(x => x.act_code === code);
    if (!p) return;
    
    const newRecents = [code, ...recents.filter(c => c !== code)].slice(0, 8);
    persistRecents(newRecents);
    
    navigate(`/bibliotheque/${code}`);
  };

  const closePanel = () => {
    navigate('/bibliotheque');
  };

  const categoriesWithCounts = useMemo(() => {
    const map = new Map<string, number>();
    CLINICAL_PROTOCOLS.forEach(p => map.set(p.category || 'Général', (map.get(p.category || 'Général') || 0) + 1));
    return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, []);

  const filtered = useMemo(() => {
    let list = [...CLINICAL_PROTOCOLS];
    if (activeCategory === 'favoris') {
      list = list.filter(p => favorites.includes(p.act_code));
    } else if (activeCategory !== 'Tous') {
      list = list.filter(p => (p.category || 'Général') === activeCategory);
    }

    if (searchTerm.trim()) {
      const q = searchTerm.trim().toLowerCase();
      list = list.filter(p =>
        p.act_names.some(n => n.toLowerCase().includes(q)) ||
        p.act_code.toLowerCase().includes(q) ||
        (p.category || 'Général').toLowerCase().includes(q)
      );
    }
    
    if (sort === 'alpha') list.sort((a, b) => a.act_names[0].localeCompare(b.act_names[0]));
    else if (sort === 'difficulty') list.sort((a, b) => DIFF_DOTS[a.difficulty as keyof typeof DIFF_DOTS] - DIFF_DOTS[b.difficulty as keyof typeof DIFF_DOTS]);
    else if (sort === 'category') list.sort((a, b) => (a.category||'').localeCompare(b.category||'') || a.act_names[0].localeCompare(b.act_names[0]));
    
    return list;
  }, [activeCategory, searchTerm, sort, favorites]);

  const cmdFiltered = useMemo(() => {
    const ql = cmdSearch.trim().toLowerCase();
    if (!ql) return CLINICAL_PROTOCOLS.slice(0, 10);
    return CLINICAL_PROTOCOLS.filter(p =>
      p.act_names.some(n => n.toLowerCase().includes(ql)) ||
      p.act_code.toLowerCase().includes(ql) ||
      (p.category || 'Général').toLowerCase().includes(ql)
    ).slice(0, 10);
  }, [cmdSearch]);

  const navProtocol = (dir: number) => {
    const list = filtered;
    const idx = list.findIndex(p => p.act_code === openProtocolCode);
    if (idx < 0) return;
    const next = list[(idx + dir + list.length) % list.length];
    openPanel(next.act_code);
  };

  const resetFilters = () => {
    setActiveCategory('Tous');
    setSearchTerm('');
    setSort('alpha');
  };

  const renderDiffDots = (diff: string) => {
    const n = DIFF_DOTS[diff as keyof typeof DIFF_DOTS] || 1;
    return (
      <span className={cn("inline-flex items-center gap-1.5", 
        diff === 'routine' ? "text-emerald-600" :
        diff === 'complex' ? "text-amber-600" : "text-rose-600"
      )}>
        {DIFF_FR[diff as keyof typeof DIFF_FR] || diff}
        <i className={cn("w-1.5 h-1.5 rounded-full", n >= 1 ? "bg-current" : "bg-slate-200")}></i>
        <i className={cn("w-1.5 h-1.5 rounded-full", n >= 2 ? "bg-current" : "bg-slate-200")}></i>
        <i className={cn("w-1.5 h-1.5 rounded-full", n >= 3 ? "bg-current" : "bg-slate-200")}></i>
      </span>
    );
  };

  const activeProtocol = openProtocolCode ? CLINICAL_PROTOCOLS.find(p => p.act_code === openProtocolCode) : null;
  const soinProtocol = soinModeCode ? CLINICAL_PROTOCOLS.find(p => p.act_code === soinModeCode) : null;

  return (
    <>
      <style>{`
        .mono { font-family: var(--font-outfit), ui-sans-serif, sans-serif; letter-spacing: 0.02em; }
        .rail::-webkit-scrollbar { width: 4px; }
        .rail::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 4px; }
        [data-theme='prestige'] .rail::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); }
        .custom-scrim { position: fixed; inset: 0; background: rgba(0,0,0,0.4); backdrop-filter: blur(4px); z-index: 50; transition: opacity 0.18s; }
        .custom-panel { 
          position: fixed; top: 0; right: 0; bottom: 0; 
          width: min(1040px, 92vw); 
          background: var(--bg-medical-pearl); 
          border-left: 1px solid var(--border-color); 
          z-index: 60; 
          display: grid; grid-template-rows: auto 1fr auto; 
          box-shadow: -30px 0 60px -30px rgba(0,0,0,0.25); 
          transition: transform 0.3s cubic-bezier(0.2, 0.7, 0.2, 1); 
        }
      `}</style>
      
      <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-[var(--bg-medical-pearl)] text-[var(--text-main)] font-sans transition-colors duration-300">
        {/* CATEGORY RAIL */}
        <aside className="hidden md:block w-[260px] flex-shrink-0 border-r border-[var(--border-color)] bg-[var(--sidebar-bg)] pt-6 px-3.5 pb-10 overflow-y-auto rail">
          <div className="text-[11px] text-[var(--text-muted)] tracking-[0.04em] font-semibold mb-4 ml-2">
            Cabinet · <b className="text-[var(--text-main)]">Bibliothèque</b>
          </div>
          <div className="space-y-1">
            <button
              onClick={() => setActiveCategory('favoris')}
              className={cn("flex items-center justify-between px-3 py-2.5 rounded-xl text-[13.5px] font-medium w-full text-left transition-all", activeCategory === 'favoris' ? "bg-[var(--text-main)] text-[var(--card-bg)] shadow-lg" : "text-[var(--text-main)] hover:bg-[var(--bg-medical-pearl)]")}
            >
              <span><span className="text-amber-500 mr-1.5">★</span> Favoris</span>
              <span className={cn("font-outfit text-[11px] font-semibold tracking-wide", activeCategory === 'favoris' ? "opacity-60" : "text-[var(--text-muted)]")}>{favorites.length}</span>
            </button>
            <button
              onClick={() => setActiveCategory('Tous')}
              className={cn("flex items-center justify-between px-3 py-2.5 rounded-xl text-[13.5px] font-medium w-full text-left transition-all", activeCategory === 'Tous' ? "bg-[var(--text-main)] text-[var(--card-bg)] shadow-lg" : "text-[var(--text-main)] hover:bg-[var(--bg-medical-pearl)]")}
            >
              <span>Tous les protocoles</span>
              <span className={cn("font-outfit text-[11px] font-semibold tracking-wide", activeCategory === 'Tous' ? "opacity-60" : "text-[var(--text-muted)]")}>{CLINICAL_PROTOCOLS.length}</span>
            </button>
          </div>
          
          <h3 className="text-[11px] uppercase tracking-[0.14em] text-[var(--text-muted)] font-bold mt-7 mb-2 ml-2">Disciplines</h3>
          <div className="space-y-0.5">
            {categoriesWithCounts.map(([cat, count]) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={cn("flex items-center justify-between px-3 py-2 rounded-xl text-[13.5px] font-medium w-full text-left transition-all", activeCategory === cat ? "bg-[var(--text-main)] text-[var(--card-bg)] shadow-md" : "text-[var(--text-main)] hover:bg-[var(--bg-medical-pearl)]")}
              >
                <span>{cat}</span>
                <span className={cn("font-outfit text-[11px] font-semibold tracking-wide", activeCategory === cat ? "opacity-60" : "text-[var(--text-muted)]")}>{count}</span>
              </button>
            ))}
          </div>
          
          <h3 className="text-[11px] uppercase tracking-[0.14em] text-[var(--text-muted)] font-bold mt-9 mb-2 ml-2">Aide</h3>
          <button onClick={() => setShowCmd(true)} className="flex items-center px-3 py-2 text-[12.5px] text-[var(--text-muted)] font-medium w-full hover:bg-[var(--bg-medical-pearl)] rounded-xl transition-colors">⌨ Raccourcis clavier</button>
          <button onClick={() => window.open('mailto:lafabriquedapollon@gmail.com?subject=Suggestion%20protocole%20DigitalCrown', '_blank')} className="flex items-center px-3 py-2 text-[var(--text-muted)] text-[12.5px] font-medium w-full hover:bg-[var(--bg-medical-pearl)] rounded-xl transition-colors">↗ Suggérer un protocole</button>
        </aside>

        {/* MAIN */}
        <main className="flex-1 overflow-y-auto px-6 md:px-11 pt-8 pb-20 custom-scrollbar">
          <div className="max-w-[1280px] mx-auto">
            <div className="flex items-center justify-between mb-1.5">
              <div className="font-outfit text-[11px] text-[var(--text-muted)] tracking-wider font-medium">/bibliotheque</div>
              <button onClick={() => setShowCmd(true)} className="inline-flex items-center gap-1.5 bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl px-3 py-2 font-outfit text-[11px] text-[var(--text-main)] font-semibold tracking-wide hover:border-[var(--text-main)] transition-all shadow-sm">
                <kbd className="bg-[var(--bg-medical-pearl)] px-1.5 py-0.5 rounded text-[10px] text-[var(--text-main)] font-sans border border-[var(--border-color)]">⌘</kbd>
                <kbd className="bg-[var(--bg-medical-pearl)] px-1.5 py-0.5 rounded text-[10px] text-[var(--text-main)] font-sans border border-[var(--border-color)]">K</kbd> 
                Rechercher
              </button>
            </div>

            <h1 className="font-serif font-medium text-4xl md:text-[54px] leading-none mb-2 tracking-tight">
              Bibliothèque <em className="italic text-[var(--primary)] font-serif">clinique</em>
            </h1>
            <p className="text-[var(--text-muted)] text-[16px] max-w-[640px] leading-relaxed mb-10">
              {CLINICAL_PROTOCOLS.length} protocoles cliniques certifiés, prêts à consulter au fauteuil. Cherche, classe, marque tes favoris, ouvre un protocole en deux clics.
            </p>


          {/* RECENTS */}
          {recents.length > 0 && (
            <section className="mb-10">
              <div className="flex items-baseline justify-between mb-4">
                <span className="text-[11px] uppercase tracking-[0.14em] text-[var(--text-muted)] font-bold">Récemment consultés</span>
                <button onClick={() => persistRecents([])} className="text-[12px] text-[var(--text-muted)] font-medium hover:text-[var(--text-main)] hover:underline">Effacer</button>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {recents.map(code => {
                  const p = CLINICAL_PROTOCOLS.find(x => x.act_code === code);
                  if (!p) return null;
                  return (
                    <button key={code} onClick={() => openPanel(code)} className="bg-[var(--card-bg)] border border-[var(--border-color)] hover:border-[var(--text-main)] hover:-translate-y-[2px] transition-all rounded-2xl p-4 flex flex-col gap-2 text-left shadow-sm">
                      <span className="font-outfit text-[10px] text-[var(--text-muted)] uppercase tracking-widest font-bold">{p.category || 'Général'}</span>
                      <span className="font-serif font-medium text-[19px] leading-snug tracking-tight text-[var(--text-main)] line-clamp-2">{p.act_names[0]}</span>
                      <span className="text-[11px] text-[var(--text-muted)] mt-auto pt-3 border-t border-[var(--border-color)]/50">
                        {DIFF_FR[p.difficulty as keyof typeof DIFF_FR]} · {p.checklist.length} points
                      </span>
                    </button>
                  );
                })}
              </div>
            </section>
          )}

          {/* TOOLBAR */}
          <div className="flex flex-col lg:flex-row lg:items-center gap-4 mb-6 pb-6 border-b border-[var(--border-color)]">
            <div className="relative flex-1 max-w-[420px]">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-lg">⌕</span>
              <input
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                placeholder="Avulsion, composite, blanchiment…"
                className="w-full py-3 pl-10 pr-12 bg-[var(--card-bg)] border border-[var(--border-color)] focus:border-[var(--text-main)] focus:ring-4 focus:ring-[var(--primary)]/10 rounded-2xl text-[14px] text-[var(--text-main)] placeholder:text-[var(--text-muted)] outline-none transition-all shadow-sm"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 font-outfit text-[10px] bg-[var(--bg-medical-pearl)] border border-[var(--border-color)] rounded-lg px-2 py-1 text-[var(--text-muted)] font-bold">⌘K</span>
            </div>

            <div className="inline-flex bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-1 shadow-sm">
              {[
                { id: 'alpha', label: 'A→Z' },
                { id: 'difficulty', label: 'Difficulté' },
                { id: 'category', label: 'Discipline' }
              ].map(opt => (
                <button
                  key={opt.id}
                  onClick={() => setSort(opt.id as any)}
                  className={cn("px-4 py-2 rounded-xl text-[12.5px] transition-all", sort === opt.id ? "bg-[var(--text-main)] text-[var(--card-bg)] font-bold shadow-md" : "text-[var(--text-muted)] font-semibold hover:text-[var(--text-main)]")}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <div className="flex-1 hidden lg:block"></div>

            <div className="flex items-center gap-5 self-end lg:self-auto">
              <span className="font-outfit text-xs text-[var(--text-muted)] font-bold uppercase tracking-wider">
                <b className="text-[var(--text-main)] font-black">{filtered.length}</b> protocoles
              </span>
              <div className="inline-flex bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-1 shadow-sm">
                <button onClick={() => setView('grid')} className={cn("w-9 h-9 flex items-center justify-center rounded-xl text-lg transition-all", view === 'grid' ? "bg-[var(--text-main)] text-[var(--card-bg)]" : "text-[var(--text-muted)] hover:text-[var(--text-main)]")} title="Vue grille">▦</button>
                <button onClick={() => setView('list')} className={cn("w-9 h-9 flex items-center justify-center rounded-xl text-lg transition-all", view === 'list' ? "bg-[var(--text-main)] text-[var(--card-bg)]" : "text-[var(--text-muted)] hover:text-[var(--text-main)]")} title="Vue liste">≡</button>
              </div>
            </div>
          </div>

          {/* GRID / LIST */}
          {filtered.length === 0 ? (
            <div className="py-24 px-5 text-center bg-[var(--card-bg)]/50 rounded-[2rem] border border-dashed border-[var(--border-color)]">
              <h3 className="font-serif font-medium text-3xl mb-3 text-[var(--text-main)]">Aucun protocole trouvé</h3>
              <p className="text-[var(--text-muted)] mb-6 text-[16px]">{searchTerm ? `Aucun résultat pour « ${searchTerm} ».` : "Aucun protocole dans cette catégorie."}</p>
              <button onClick={resetFilters} className="inline-flex items-center gap-2 bg-[var(--text-main)] text-[var(--card-bg)] px-6 py-3 rounded-2xl text-[14px] font-bold hover:scale-105 active:scale-95 transition-all shadow-xl shadow-[var(--text-main)]/10">
                ↺ Réinitialiser les filtres
              </button>
            </div>
          ) : (
            <div className={cn(view === 'grid' ? "grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4" : "flex flex-col bg-[var(--card-bg)] rounded-3xl border border-[var(--border-color)] overflow-hidden shadow-sm")}>
              {filtered.map((p, idx) => {
                const isFav = favorites.includes(p.act_code);
                const nCrit = p.checklist.filter(c => c.critical).length;
                
                if (view === 'list') {
                  return (
                    <button key={p.act_code} onClick={() => openPanel(p.act_code)} className={cn("grid grid-cols-[1.4fr_140px_1fr_auto] items-center gap-6 p-5 border-b border-[var(--border-color)]/50 hover:bg-[var(--bg-medical-pearl)] transition-colors text-left group", idx === filtered.length - 1 && "border-b-0")}>
                      <span>
                        <span className="font-outfit text-[11px] text-[var(--text-muted)] uppercase tracking-wider font-bold">{p.category || 'Général'}</span><br/>
                        <span className="font-serif font-medium text-[19px] leading-snug text-[var(--text-main)]">{p.act_names[0]}</span>
                      </span>
                      <span className="text-[13.5px]">{renderDiffDots(p.difficulty)}</span>
                      <span className="font-outfit text-[11.5px] text-[var(--text-muted)] font-medium">
                        {p.checklist.length} étapes · {p.pitfalls.length} risque{p.pitfalls.length > 1 ? 's' : ''}
                      </span>
                      <div className="flex items-center gap-4">
                        <span onClick={e => toggleFav(e, p.act_code)} className={cn("text-xl transition-all hover:scale-125", isFav ? "text-amber-500" : "text-[var(--border-color)] hover:text-amber-300")}>
                          {isFav ? '★' : '☆'}
                        </span>
                        <span className="text-[var(--primary)] text-xl opacity-0 group-hover:opacity-100 transition-all translate-x-2 group-hover:translate-x-0">→</span>
                      </div>
                    </button>
                  );
                }

                return (
                  <button key={p.act_code} onClick={() => openPanel(p.act_code)} className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-[20px] p-5 text-left relative flex flex-col gap-4 hover:border-[var(--text-main)] hover:-translate-y-1 hover:shadow-xl hover:shadow-[var(--text-main)]/5 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--primary)]/20 transition-all group">
                    <div className="flex items-center justify-between font-outfit text-[11px] text-[var(--text-muted)] tracking-wider uppercase font-bold">
                      <span className="text-[var(--primary)]">{p.category || 'Général'}</span>
                      <span onClick={e => toggleFav(e, p.act_code)} className={cn("text-[20px] w-8 h-8 flex items-center justify-center rounded-xl transition-all hover:bg-amber-50", isFav ? "text-amber-500" : "text-[var(--border-color)] hover:text-amber-500")}>
                        {isFav ? '★' : '☆'}
                      </span>
                    </div>
                    <h3 className="font-serif font-medium text-[24px] leading-tight tracking-tight m-0 text-[var(--text-main)] line-clamp-2">{p.act_names[0]}</h3>
                    <div className="flex items-center gap-3 text-[var(--text-main)] text-[13.5px] font-semibold">
                      {renderDiffDots(p.difficulty)}
                      {p.pitfalls.length > 0 && (
                        <>
                          <span className="w-1 h-1 rounded-full bg-[var(--text-muted)]"></span>
                          <span className="text-rose-600">{p.pitfalls.length} risque{p.pitfalls.length > 1 ? 's' : ''}</span>
                        </>
                      )}
                    </div>
                    <div className="mt-auto pt-4 border-t border-[var(--border-color)]/60 flex justify-between items-center">
                      <span className="font-outfit text-[12px] text-[var(--text-muted)] font-bold uppercase tracking-wide">
                        {p.checklist.length} étapes
                        {nCrit > 0 && <span className="text-rose-600"> · {nCrit} critiques</span>}
                      </span>
                      <span className="text-[13px] text-[var(--primary)] font-bold opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all">Consulter →</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
          </div>
        </main>
      </div>

      {/* DETAIL PANEL */}
      {openProtocolCode && activeProtocol && (
        <>
          <div className="custom-scrim" onClick={closePanel} />
          <aside className="custom-panel">
            <header className="flex items-center justify-between px-8 py-5 border-b border-[var(--border-color)] bg-[var(--card-bg)]">
              <div className="flex items-center gap-4 font-outfit text-[11px] text-[var(--text-muted)] tracking-widest uppercase font-black">
                <span className="text-[var(--primary)]">{activeProtocol.category || 'Général'}</span>
                <span className="opacity-40">/</span>
                <span className="text-[var(--text-main)]">{activeProtocol.act_code}</span>
                <div className="flex gap-1 ml-4">
                  <button onClick={() => navProtocol(-1)} className="w-8 h-8 border border-[var(--border-color)] rounded-xl flex items-center justify-center text-[var(--text-main)] bg-[var(--card-bg)] hover:border-[var(--text-main)] transition-all" title="Précédent (←)">‹</button>
                  <button onClick={() => navProtocol(1)} className="w-8 h-8 border border-[#e6e8ec] rounded-xl flex items-center justify-center text-[var(--text-main)] bg-[var(--card-bg)] hover:border-[var(--text-main)] transition-all" title="Suivant (→)">›</button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={(e) => toggleFav(e, activeProtocol.act_code)} className="px-4 py-2 border border-[var(--border-color)] rounded-xl text-[13px] font-bold text-[var(--text-main)] bg-[var(--card-bg)] hover:border-[var(--text-main)] transition-all inline-flex items-center gap-2">
                  <span className={cn("text-lg", favorites.includes(activeProtocol.act_code) ? "text-amber-500" : "")}>{favorites.includes(activeProtocol.act_code) ? '★' : '☆'}</span> 
                  {favorites.includes(activeProtocol.act_code) ? 'Favori' : 'Mettre en favori'}
                </button>
                <button onClick={() => window.print()} className="w-10 h-10 border border-[var(--border-color)] rounded-xl flex items-center justify-center text-[var(--text-main)] bg-[var(--card-bg)] hover:border-[var(--text-main)] transition-all" title="Imprimer (P)">⎙</button>
                <button onClick={closePanel} className="w-10 h-10 bg-[var(--text-main)] text-[var(--card-bg)] rounded-xl flex items-center justify-center text-xl font-light hover:scale-105 transition-all ml-2" title="Fermer (Esc)">×</button>
              </div>
            </header>

            <div className="flex-1 overflow-y-auto px-10 py-10 bg-[var(--card-bg)]">
              <div className="max-w-[800px] mx-auto">
                <ClinicalRefContent protocol={activeProtocol} />
              </div>
            </div>

            <footer className="px-8 py-5 bg-[var(--bg-medical-pearl)] border-t border-[var(--border-color)] flex justify-between items-center text-[11px] text-[var(--text-muted)] font-bold uppercase tracking-widest">
              <div className="flex gap-6 items-center">
                <span className="flex gap-2 items-center"><kbd className="bg-[var(--card-bg)] px-2 py-1 rounded-lg text-[var(--text-main)] border border-[var(--border-color)] shadow-sm">←</kbd><kbd className="bg-[var(--card-bg)] px-2 py-1 rounded-lg text-[var(--text-main)] border border-[var(--border-color)] shadow-sm">→</kbd> Naviguer</span>
                <span className="flex gap-2 items-center"><kbd className="bg-[var(--card-bg)] px-2 py-1 rounded-lg text-[var(--text-main)] border border-[var(--border-color)] shadow-sm">Esc</kbd> Fermer</span>
              </div>
              <button 
                onClick={() => setSoinModeCode(openProtocolCode)}
                className="bg-[var(--primary)] text-white px-5 py-2.5 rounded-xl text-[13px] font-black tracking-normal normal-case hover:scale-105 transition-all shadow-lg shadow-[var(--primary)]/20"
              >
                ↗ Ouvrir en mode Soin
              </button>
            </footer>
          </aside>
        </>
      )}

      {/* COMMAND PALETTE */}
      {showCmd && (
        <div className="fixed inset-0 bg-[var(--medical-dark)]/40 backdrop-blur-sm z-[100] flex justify-center pt-[12vh] px-4 animate-in fade-in duration-200" onClick={(e) => { if(e.target === e.currentTarget) setShowCmd(false); }}>
          <div className="w-full max-w-[640px] h-fit bg-[var(--card-bg)] rounded-[2rem] shadow-2xl border border-[var(--border-color)] overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="flex items-center gap-4 px-6 py-5 border-b border-[var(--border-color)]">
              <span className="text-[var(--text-muted)] text-2xl font-light">⌕</span>
              <input
                ref={cmdInputRef}
                value={cmdSearch}
                onChange={e => setCmdSearch(e.target.value)}
                placeholder="Rechercher un protocole ou une spécialité..."
                className="flex-1 border-0 outline-none text-lg text-[var(--text-main)] placeholder:text-[var(--text-muted)] bg-transparent font-medium"
              />
              <kbd className="font-outfit bg-[var(--bg-medical-pearl)] px-2.5 py-1 rounded-xl text-[11px] text-[var(--text-muted)] border border-[var(--border-color)] uppercase font-black">esc</kbd>
            </div>
            <div className="max-h-[60vh] overflow-y-auto p-3">
              {cmdFiltered.length === 0 ? (
                <div className="py-12 text-center text-[var(--text-muted)] font-medium">Aucun protocole ne correspond à votre recherche.</div>
              ) : (
                <div className="grid gap-1">
                  {cmdFiltered.map((p, i) => (
                    <button
                      key={p.act_code}
                      onClick={() => { setShowCmd(false); openPanel(p.act_code); }}
                      className={cn("w-full grid grid-cols-[1fr_auto] gap-4 px-4 py-3.5 rounded-2xl cursor-pointer items-center text-left transition-all", i === 0 && !cmdSearch ? "bg-[var(--bg-medical-pearl)]" : "hover:bg-[var(--bg-medical-pearl)]")}
                    >
                      <div>
                        <div className="text-[15px] text-[var(--text-main)] font-bold">{p.act_names[0]}</div>
                        <div className="text-[11px] text-[var(--text-muted)] font-medium uppercase tracking-wider">{p.act_code}</div>
                      </div>
                      <span className="font-outfit text-[10px] bg-[var(--primary)]/10 text-[var(--primary)] px-2.5 py-1 rounded-lg uppercase tracking-widest font-black">{p.category || 'Général'}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="px-6 py-3 bg-[var(--bg-medical-pearl)] border-t border-[var(--border-color)] flex justify-between items-center text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-widest">
              <span>Appuyez sur <b className="text-[var(--text-main)]">Entrée</b> pour ouvrir</span>
              <div className="flex gap-4">
                <span><b className="text-[var(--text-main)]">↑↓</b> Naviguer</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODE SOIN IMMERSIF */}
      <AnimatePresence>
        {soinModeCode && soinProtocol && (
          <ClinicalSoinMode 
            protocol={soinProtocol} 
            onClose={() => setSoinModeCode(null)} 
          />
        )}
      </AnimatePresence>
    </>
  );
};
