
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// --- TAB 1: PROFIL (Index 542 to 1172) ---
// Ends with 5 divs
lines[1168] = "                </div>";
lines[1169] = "              </div>";
lines[1170] = "            </div>";
lines[1171] = "          </div>";
lines[1172] = "        </div>";
lines[1173] = "      )}";
lines[1174] = "    )}";

// --- TAB 2: BRANDING (Index 1176 to 1532) ---
// Ends with 4 divs
lines[1529] = "                </div>";
lines[1530] = "              </div>";
lines[1531] = "            </div>";
lines[1532] = "          </div>";
lines[1533] = "        )}";

// --- TAB 3: IA (Index 1536 to 1620) ---
// IA was already balanced at 7 closures.
lines[1613] = "                    </div>";
lines[1614] = "                  </div>";
lines[1615] = "                </div>";
lines[1616] = "              </div>";
lines[1617] = "            </div>";
lines[1618] = "          </div>";
lines[1619] = "        </div>";
lines[1620] = "      )}";

// --- TAB 4: SECURITE (Index 1621 to 1643) ---
// Needs 2 closures
lines[1640] = "                  </div>";
lines[1641] = "                </div>";
lines[1642] = "              )}";

// --- TAB 5: EQUIPE (Index 1644 to 1648) ---
// Needs 1 closure
lines[1647] = "                  </div>";
lines[1648] = "                )}";

// --- FINAL CLOSURES ---
lines[1649] = "            </div>";
lines[1650] = "          </div>";
lines[1651] = "        </div>";
lines[1652] = "      </div>";
lines[1653] = "    );";
lines[1654] = "};";
lines[1655] = "export default Settings;";

fs.writeFileSync(path, lines.slice(0, 1656).join('\n'));
