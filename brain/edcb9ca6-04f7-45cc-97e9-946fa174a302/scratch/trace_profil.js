
import fs from 'fs';

const content = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');
const lines = content.split('\n');
let currentBalance = 0;
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith('//')) continue;
    const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
    const closes = (line.match(/<\/div>/g) || []).length;
    currentBalance += (opens - closes);
    
    if (i >= 543 && i <= 1170) {
        if (opens > 0 || closes > 0) {
            // console.log(`${i + 1}: ${currentBalance} (Diff: ${opens - closes})`);
        }
    }
}

// Re-run specifically for Profil tab to find jumps
currentBalance = 0;
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith('//')) continue;
    const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
    const closes = (line.match(/<\/div>/g) || []).length;
    currentBalance += (opens - closes);
    
    if (i >= 543 && i <= 1170) {
        if (opens !== closes) {
            console.log(`Line ${i+1} balance change: ${opens - closes} | New Balance: ${currentBalance}`);
        }
    }
}
