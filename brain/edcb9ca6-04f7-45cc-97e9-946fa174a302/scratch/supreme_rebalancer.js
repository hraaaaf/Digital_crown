
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
}

console.log("Current balance:", balance);

if (balance < 0) {
    console.log("Removing", -balance, "extra closures...");
    // Find the last N closures and remove them
    let removed = 0;
    for (let i = lines.length - 1; i >= 0 && removed < -balance; i--) {
        if (lines[i].trim() === '</div>') {
            lines[i] = "";
            removed++;
        }
    }
} else if (balance > 0) {
    console.log("Adding", balance, "missing closures...");
    for (let i = 0; i < balance; i++) {
        lines.splice(lines.length - 3, 0, "      </div>");
    }
}

fs.writeFileSync(path, lines.join('\n'));
