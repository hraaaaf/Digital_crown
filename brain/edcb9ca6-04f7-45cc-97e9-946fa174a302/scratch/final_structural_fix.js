
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Keep everything before the mess starts (around line 1612, which is index 1611)
const newLines = lines.slice(0, 1611);

// Append the correct tail
newLines.push(
`                  </div>
                </div>
              )}

              {/* TAB 4 : SÉCURITÉ */}
              {activeTab === 'securite' && (
                <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
                  <div className="mb-8 pb-6 border-b border-slate-100">
                    <h3 className="text-2xl font-black flex items-center gap-3" style={{ color: 'var(--primary)' }}><Database className="text-emerald-500" /> Gestion des Données</h3>
                    <p className="text-slate-500 text-sm font-medium mt-2">Digital Crown garantit la souveraineté de vos données cliniques (SQLite Locale).</p>
                  </div>

                  <div className="bg-slate-50 border border-slate-200 rounded-2xl p-8 flex flex-col items-center justify-center text-center gap-4">
                    <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-sm text-slate-700">
                      <Database size={32} />
                    </div>
                    <div>
                      <h4 className="font-black text-lg text-slate-800">Sauvegarde Complète (Backup)</h4>
                      <p className="text-sm text-slate-500 max-w-md mx-auto mt-2">Exportez l'intégralité de la base de données patients, radios et analyses dans un format sécurisé.</p>
                    </div>
                    <button 
                      onClick={handleExportDB}
                      className="mt-4 px-8 py-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-black transition-all shadow-xl shadow-emerald-600/20 flex items-center gap-3"
                    >
                      <Download size={20} /> Exporter la Base de Données
                    </button>
                  </div>
                </div>
              )}

              {/* TAB 5 : MON ÉQUIPE */}
              {activeTab === 'equipe' && (
                <div className="animate-in slide-in-from-right-4 duration-500">
                  <TeamManager />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
};

export default Settings;`
);

fs.writeFileSync(path, newLines.join('\n'));
