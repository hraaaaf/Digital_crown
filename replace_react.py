import sys

file_path = "frontend/src/features/admin/components/LiveDocumentStudio.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the specific block
old_block = """            {selectedTemplate === 'sidebar' && (
              <>
                <div className="flex-col items-center justify-center pt-8 shrink-0">
                  {resolvedLogo ? (
                    <img src={resolvedLogo} className="w-16 h-16 object-contain" alt="Logo" />
                  ) : (
                    <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center border border-slate-100"><ImageIcon className="text-slate-200" size={24} /></div>
                  )}
                </div>
                <div className="flex-1 space-y-2 pr-4">
                  <h4 className="font-black leading-none uppercase tracking-tighter" style={{ color: brandColor, fontSize: `${14 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                  {identity.nomPraticienAR && <h4 className="font-black font-arabic" style={{ color: brandColor, fontSize: `${16 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                  <p className="font-extrabold uppercase tracking-widest opacity-70" style={{ fontSize: `${8 * headerScale}px`, color: secondaryColor }}>{specialtyStrings.fr || 'Chirurgien Dentiste'}</p>
                </div>
              </>
            )}

            {selectedTemplate === 'royal' && (
              <div className="flex flex-col items-center w-full gap-3">
                {resolvedLogo ? (
                  <img src={resolvedLogo} className="w-16 h-16 object-contain drop-shadow-lg" alt="Logo" />
                ) : (
                  <div className="w-14 h-14 bg-white rounded-full flex items-center justify-center border-2 border-double shadow-sm" style={{ borderColor: brandColor }}><Sparkles style={{ color: brandColor }} size={24} /></div>
                )}
                <div className="flex items-center gap-4 w-full">
                   <div className="h-[1px] flex-1" style={{ backgroundImage: `linear-gradient(to right, transparent, ${brandColor}40)` }} />
                   <div className="text-center">
                      <h4 className="font-black uppercase tracking-[0.1em] leading-none" style={{ color: brandColor, fontSize: `${15 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                      {identity.nomPraticienAR && <h4 className="font-black font-arabic mt-1" style={{ color: brandColor, fontSize: `${17 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                   </div>
                   <div className="h-[1px] flex-1" style={{ backgroundImage: `linear-gradient(to left, transparent, ${brandColor}40)` }} />
                </div>
              </div>
            )}

            {selectedTemplate === 'royal' && (
              <>
                <div className="text-left space-y-1">
                  <h4 className="font-black uppercase tracking-tight leading-none" style={{ color: brandColor, fontSize: `${11 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM'}</h4>
                  <p className="font-extrabold uppercase" style={{ color: secondaryColor, fontSize: `${7 * headerScale}px` }}>Dentiste</p>
                  <p className="font-medium opacity-50 leading-tight" style={{ fontSize: `${6 * headerScale}px`, color: secondaryColor }}>{specialtyStrings.fr || 'Spécialités'}</p>
                </div>

                <div className="flex flex-col items-center">
                  {resolvedLogo ? (
                    <img src={resolvedLogo} className="w-12 h-12 object-contain" alt="Logo" />
                  ) : (
                    <div className="w-10 h-10 bg-white border border-slate-100 rounded-xl flex items-center justify-center"><ImageIcon className="text-slate-100" size={18} /></div>
                  )}
                </div>

                <div className="text-right" dir="rtl">
                  <h4 className="font-black tracking-tight font-arabic leading-none" style={{ color: brandColor, fontSize: `${12 * headerScale}px` }}>د. {identity.nomPraticienAR || 'الاسم'}</h4>
                  <p className="font-extrabold" style={{ color: secondaryColor, fontSize: `${8 * headerScale}px` }}>طبيب أسنان</p>
                  <p className="font-arabic opacity-50 leading-tight" style={{ fontSize: `${7 * headerScale}px`, color: secondaryColor }}>{specialtyStrings.ar || 'التخصصات'}</p>
                </div>
              </>
            )}

            {selectedTemplate === 'swiss' && (
              <div className={cn(
                "flex-1 flex items-center gap-6",
                selectedTemplate === 'prestige' && "flex-col",
                selectedTemplate === 'minimal' && "justify-between w-full"
              )}>
                {resolvedLogo ? (
                  <img src={resolvedLogo} className={cn("object-contain", selectedTemplate === 'minimal' ? "w-10 h-10" : "w-14 h-14")} alt="Logo" />
                ) : (
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center border border-slate-50 shadow-sm"><ImageIcon className="text-slate-200" size={20} /></div>
                )}
                
                <div className={cn(selectedTemplate === 'prestige' && "text-center", "space-y-1")}>
                  <h4 className="font-black uppercase tracking-tight leading-none" style={{ color: brandColor, fontSize: `${14 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                  {identity.nomPraticienAR && <h4 className="font-black font-arabic" style={{ color: brandColor, fontSize: `${16 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                  <p className="font-bold uppercase tracking-widest opacity-60" style={{ fontSize: `${8 * headerScale}px`, color: secondaryColor }}>{specialtyStrings.fr || 'Chirurgien Dentiste'}</p>
                </div>
              </div>
            )}"""

new_block = """            {selectedTemplate === 'royal' && (
              <div className="flex flex-col items-center w-full gap-3 py-6">
                {resolvedLogo ? (
                  <img src={resolvedLogo} className="w-16 h-16 object-contain drop-shadow-lg" alt="Logo" />
                ) : (
                  <div className="w-14 h-14 bg-white rounded-full flex items-center justify-center border-2 border-double shadow-sm" style={{ borderColor: brandColor }}><Sparkles style={{ color: brandColor }} size={24} /></div>
                )}
                <div className="flex items-center gap-4 w-full px-8">
                   <div className="h-[1px] flex-1" style={{ backgroundImage: `linear-gradient(to right, transparent, ${brandColor}40)` }} />
                   <div className="text-center">
                      <h4 className="font-black uppercase tracking-[0.1em] leading-none" style={{ color: brandColor, fontSize: `${15 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                      {identity.nomPraticienAR && <h4 className="font-black font-arabic mt-1" style={{ color: brandColor, fontSize: `${17 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                   </div>
                   <div className="h-[1px] flex-1" style={{ backgroundImage: `linear-gradient(to left, transparent, ${brandColor}40)` }} />
                </div>
              </div>
            )}

            {selectedTemplate === 'swiss' && (
              <div className="flex-1 flex items-center gap-6 py-6 px-4">
                {resolvedLogo ? (
                  <img src={resolvedLogo} className="object-contain w-14 h-14" alt="Logo" />
                ) : (
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center border border-slate-50 shadow-sm"><ImageIcon className="text-slate-200" size={20} /></div>
                )}
                
                <div className="space-y-1 text-left">
                  <h4 className="font-black uppercase tracking-tight leading-none" style={{ color: brandColor, fontSize: `${14 * headerScale}px` }}>{identity.nomPraticien || 'DR. NOM DE FAMILLE'}</h4>
                  {identity.nomPraticienAR && <h4 className="font-black font-arabic" style={{ color: brandColor, fontSize: `${16 * headerScale}px` }}>د. {identity.nomPraticienAR}</h4>}
                  <p className="font-bold uppercase tracking-widest opacity-60" style={{ fontSize: `${8 * headerScale}px`, color: secondaryColor }}>{specialtyStrings.fr || 'Chirurgien Dentiste'}</p>
                </div>
              </div>
            )}"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Block not found!")
