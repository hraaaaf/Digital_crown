
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
    
    // Check points - Ensure balance is 4 before starting a new tab
    if (line.includes('{/* TAB 2 : DESIGN & AMBIANCE */}')) {
        if (balance > 4) {
            lines[i-1] = "        " + "</div>".repeat(balance - 4) + "\n        )}";
            balance = 4;
        }
    }
    if (line.includes('{/* TAB 3 : OPTIMISATION & SYSTÈME */}')) {
        if (balance > 4) {
            lines[i-1] = "        " + "</div>".repeat(balance - 4) + "\n        )}";
            balance = 4;
        }
    }
    if (line.includes('{/* TAB 3 : SÉCURITÉ */}')) {
        if (balance > 4) {
            lines[i-1] = "        " + "</div>".repeat(balance - 4) + "\n        )}";
            balance = 4;
        }
    }
    if (line.includes('{/* TAB 5 : MON ÉQUIPE */}')) {
        if (balance > 4) {
            lines[i-1] = "        " + "</div>".repeat(balance - 4) + "\n        )}";
            balance = 4;
        }
    }
}

// Final reconciliation
if (balance > 0) {
    // Add missing closures before );
    let target = lines.length - 1;
    for (let i = lines.length - 1; i >= 0; i--) {
        if (lines[i].includes(');')) {
            target = i;
            break;
        }
    }
    lines.splice(target, 0, "</div>".repeat(balance));
} else if (balance < 0) {
    // Remove extra closures from the end
    let removed = 0;
    for (let i = lines.length - 1; i >= 0 && removed < -balance; i--) {
        if (lines[i].trim() === '</div>') {
            lines[i] = "";
            removed++;
        }
    }
}

fs.writeFileSync(path, lines.join('\n'));
