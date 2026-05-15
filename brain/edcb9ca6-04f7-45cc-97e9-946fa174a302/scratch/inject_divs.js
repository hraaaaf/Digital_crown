
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// IA fix (L1612-1615)
// Add 3 divs
lines[1614] = "            </div>";
lines.splice(1615, 0, "          </div>", "        </div>", "      </div>");

// Securite fix (L1641-1642 roughly, but indices change after splice)
// Let's find it by context.
let securiteIndex = -1;
for (let i = 1600; i < lines.length; i++) {
    if (lines[i].includes('Download size={20} /> Exporter la Base de Données')) {
        // It's after the button
        for (let j = i; j < i + 10; j++) {
            if (lines[j].trim() === '</div>' && lines[j+1].trim() === '</div>') {
                securiteIndex = j + 1;
                break;
            }
        }
        break;
    }
}

if (securiteIndex !== -1) {
    lines.splice(securiteIndex + 1, 0, "            </div>");
}

fs.writeFileSync(path, lines.join('\n'));
