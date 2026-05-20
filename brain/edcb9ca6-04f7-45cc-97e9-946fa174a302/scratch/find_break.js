
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
    
    if (currentBalance < 0) {
        console.log(`Balance broke at line ${i + 1}: ${currentBalance}`);
        console.log(`Line: ${line.trim()}`);
        process.exit(1);
    }
}
console.log('Final Balance:', currentBalance);
