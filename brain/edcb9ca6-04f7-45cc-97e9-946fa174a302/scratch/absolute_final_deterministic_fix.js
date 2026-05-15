
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

function getBalanceAt(lineIndex) {
    let b = 0;
    for (let i = 0; i <= lineIndex; i++) {
        const l = lines[i];
        if (!l) continue;
        const o = (l.match(/<div(?![^>]*\/>)/g) || []).length;
        const c = (l.match(/<\/div>/g) || []).length;
        b += (o - c);
    }
    return b;
}

// 1. Profil (Start L543, End L1173)
// Balance at 542 (before start): 4
// We want balance 4 at 1172 (before first closure)
// Currently at 1171 it is 4? Let's check.
// Wait, I'll just clear the area and write the closures.

const fixTab = (startIndex, endIndex, targetBalance) => {
    // startIndex and endIndex are 1-based line numbers
    let currentB = getBalanceAt(startIndex - 2); // balance before start
    // We want to remove all existing divs at the end and replace them with exactly the right number.
    // Actually, let's just count the internal balance.
    let internalB = 0;
    for (let i = startIndex - 1; i < endIndex - 2; i++) {
        const l = lines[i];
        const o = (l.match(/<div(?![^>]*\/>)/g) || []).length;
        const c = (l.match(/<\/div>/g) || []).length;
        internalB += (o - c);
    }
    // internalB should be 0.
    // If internalB > 0, we need closures.
    return internalB;
};

// I will just manually fix the 5 points.

// Profil: Balance at 1172 should be 4.
// Let's check balance at 1167.
let b1167 = getBalanceAt(1166); // L1167 is index 1166
// If b1167 is 8. Then 1168, 1169, 1170, 1171 bring it to 4.
lines[1171] = "                </div>";
lines[1172] = "              </div>";

// Branding: 
let b1525 = getBalanceAt(1524); // L1525 is index 1524
// If b1525 is 7. Then 1526, 1527, 1530 bring it to 4.
lines[1529] = "                </div>";
lines[1530] = "              </div>";

// IA:
let b1611 = getBalanceAt(1610); // L1611 is index 1610
// If b1611 is 10. Then 1612, 1613, 1614, 1615, 1616, 1617 bring it to 4.
lines[1611] = "                  </div>";
lines[1612] = "                </div>";
lines[1613] = "              </div>";
lines[1614] = "            </div>";
lines[1615] = "          </div>";
lines[1616] = "        </div>";

// Securite:
let b1638 = getBalanceAt(1637); // L1638 is index 1637
// If b1638 is 6? Let's check.
lines[1638] = "                  </button>";
lines[1639] = "                </div>";
lines[1640] = "              </div>";

// Equipe:
lines[1645] = "                  <TeamManager />";
lines[1646] = "                </div>";

// Final:
lines[1648] = "            </div>";
lines[1649] = "          </div>";
lines[1650] = "        </div>";
lines[1651] = "      </div>";
lines[1652] = "    );";
lines[1653] = "};";

fs.writeFileSync(path, lines.join('\n'));
