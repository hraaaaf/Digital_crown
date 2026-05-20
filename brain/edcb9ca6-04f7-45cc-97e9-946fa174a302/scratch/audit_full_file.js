
import fs from 'fs';

const content = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');
const lines = content.split('\n');

let balance = 0;
let results = [];

for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
    const closes = (line.match(/<\/div>/g) || []).length;
    balance += (opens - closes);
    results.push({ line: i + 1, diff: opens - closes, total: balance, text: line.trim() });
}

// Filter for lines with changes or high balance
results.filter(r => r.diff !== 0 || r.line > 1650).forEach(r => {
    console.log(`L${r.line}: Diff ${r.diff} | Total ${r.total} | ${r.text.substring(0, 50)}`);
});

console.log("Final Balance:", balance);
