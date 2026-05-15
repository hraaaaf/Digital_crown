
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// --- 1. Fix Profil Tab (End L1175) ---
// We need 5 internal closures for Profil.
lines[1171] = "            </div>";
lines[1172] = "          </div>";
lines[1173] = "        )}";
lines[1174] = "      )}";
lines[1175] = ""; // Clear the extra lines

// --- 2. Fix Branding Tab (End L1533) ---
// Currently balance at end of Branding is 5. We need 4.
// So we add one more </div> before )}.
lines[1529] = "                </div>";
lines[1530] = "              </div>";
lines[1531] = "            </div>";
lines[1532] = "          </div>";
lines[1533] = "        )}";

// --- 3. Fix Securite Tab (Missing closure!) ---
// Securite starts at L1622.
// It should end before TAB 5 (L1645).
// We'll insert the closures at L1644.
lines[1641] = "                </div>";
lines[1642] = "              </div>";
lines[1643] = "            )}";
lines[1644] = ""; // Keep it clean

// --- 4. Final Closures (L1650-1655) ---
// Balance should be 4 before these lines.
lines[1649] = "            </div>";
lines[1650] = "          </div>";
lines[1651] = "        </div>";
lines[1652] = "      </div>";
lines[1653] = "    );";
lines[1654] = "};";
lines[1655] = "export default Settings;";

fs.writeFileSync(path, lines.join('\n'));
