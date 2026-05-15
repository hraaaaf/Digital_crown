
import fs from 'fs';

const content = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');
const lines = content.split('\n');

function checkBalance(startLine, endLine) {
    let balance = 0;
    for (let i = startLine - 1; i < endLine; i++) {
        const line = lines[i];
        if (!line) continue;
        const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
        const closes = (line.match(/<\/div>/g) || []).length;
        balance += (opens - closes);
        if (opens !== 0 || closes !== 0) {
            console.log(`L${i + 1}: ${line.trim()} | Diff: ${opens - closes} | Total: ${balance}`);
        }
    }
    return balance;
}

console.log("--- PROFIL TAB ---");
checkBalance(543, 1171);

console.log("\n--- BRANDING TAB ---");
checkBalance(1174, 1529);

console.log("\n--- IA TAB ---");
checkBalance(1534, 1645);
