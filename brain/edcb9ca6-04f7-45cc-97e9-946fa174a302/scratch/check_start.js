
import fs from 'fs';

const content = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');
const lines = content.split('\n');
let currentBalance = 0;
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith('//')) continue;
    const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
    const closes = (line.match(/<\/div>/g) || []).length;
    const diff = opens - closes;
    currentBalance += diff;
    
    if (diff > 0) {
        // console.log(`Line ${i+1} opens ${diff} div(s). New balance: ${currentBalance}`);
    } else if (diff < 0) {
        // console.log(`Line ${i+1} closes ${-diff} div(s). New balance: ${currentBalance}`);
    }
    
    if (i === 498) console.log(`Balance at return start (499): ${currentBalance}`);
    if (i === 541) console.log(`Balance at tab 1 start (542): ${currentBalance}`);
}
