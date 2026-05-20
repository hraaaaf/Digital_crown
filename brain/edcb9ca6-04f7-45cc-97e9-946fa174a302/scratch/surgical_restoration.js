
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// --- 1. Fix IA Tab End (L1613-1621) ---
// It should only close its internal divs and then )}.
// IA starts at L1538.
// L1539: div 1 (space-y-8)
// L1545: div 2 (space-y-8)
// L1546: div 3 (bg-slate-50)
// L1572: div 3 (bg-slate-50)
// L1591: div 3 (bg-slate-50)
lines[1612] = "                </div>";
lines[1613] = "              </div>";
lines[1614] = "            )}";
lines[1615] = "";
lines[1616] = "";
lines[1617] = "";
lines[1618] = "";
lines[1619] = "";
lines[1620] = "";

// --- 2. Fix Securite Tab (Re-injecting the header) ---
lines[1621] = `
              {/* TAB 4 : SÉCURITÉ */}
              {activeTab === 'securite' && (
                <div className="space-y-8 animate-in slide-in-from-right-4 duration-500">
                  <div className="mb-8 pb-6 border-b border-slate-100">`;

// --- 3. Fix Securite Tab End (L1641-1643) ---
lines[1640] = "                </div>";
lines[1641] = "              </div>";
lines[1642] = "            )}";

// --- 4. Fix Equipe Tab (Re-injecting the header) ---
lines[1643] = `
              {/* TAB 5 : MON ÉQUIPE */}
              {activeTab === 'equipe' && (` ;

// --- 5. Fix Equipe Tab End (L1649) ---
lines[1648] = "                </div>";
lines[1649] = "              )}";

// --- 6. Final Closures (L1650-1653) ---
lines[1650] = "            </div>";
lines[1651] = "          </div>";
lines[1652] = "        </div>";
lines[1653] = "      </div>";

fs.writeFileSync(path, lines.join('\n'));
