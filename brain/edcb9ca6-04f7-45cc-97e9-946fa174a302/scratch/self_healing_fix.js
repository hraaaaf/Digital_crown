
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

let balance = 0;
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
    const closes = (line.match(/<\/div>/g) || []).length;
    balance += (opens - closes);
    
    // Check points
    // Profil end (L1173)
    if (i + 1 === 1173) {
        if (balance > 4) {
            lines[i] = "                " + "</div>".repeat(balance - 4) + "\n              )}";
            balance = 4;
        } else if (balance < 4) {
            lines[i] = "                " + "<div>".repeat(4 - balance) + "\n              )}";
            balance = 4;
        }
    }
    
    // Branding end (L1532)
    if (i + 1 === 1532) {
        if (balance > 4) {
            lines[i] = "                " + "</div>".repeat(balance - 4) + "\n              )}";
            balance = 4;
        }
    }
    
    // IA end (L1619)
    if (i + 1 === 1619) {
        if (balance > 4) {
            lines[i] = "                " + "</div>".repeat(balance - 4) + "\n              )}";
            balance = 4;
        }
    }
    
    // Securite end (L1641)
    if (i + 1 === 1641) {
        if (balance > 4) {
            lines[i] = "                " + "</div>".repeat(balance - 4) + "\n              )}";
            balance = 4;
        }
    }
}

// Final closures
const lastLine = lines.length - 1;
if (balance > 0) {
    lines.push("</div>".repeat(balance));
    lines.push(");");
    lines.push("};");
    lines.push("export default Settings;");
}

fs.writeFileSync(path, lines.join('\n'));
