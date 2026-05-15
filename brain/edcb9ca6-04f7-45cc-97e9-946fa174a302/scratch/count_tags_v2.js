
import fs from 'fs';

const content = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');

const lines = content.split('\n');
let currentBalance = 0;
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    // Ignore comments
    if (line.trim().startsWith('//') || line.trim().startsWith('/*') || line.trim().startsWith('*')) continue;
    
    const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
    const closes = (line.match(/<\/div>/g) || []).length;
    currentBalance += (opens - closes);
    
    if (i > 1000 && i < 1200) {
        // console.log(`${i + 1}: ${line.trim()} | Balance: ${currentBalance}`);
    }
    
    if (currentBalance > 10) {
        // console.log(`High balance at line ${i+1}: ${currentBalance}`);
    }
}
console.log('Final Balance:', currentBalance);

// Find blocks where balance increases a lot
currentBalance = 0;
let maxBalance = 0;
let maxLine = 0;
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith('//')) continue;
    const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
    const closes = (line.match(/<\/div>/g) || []).length;
    currentBalance += (opens - closes);
    if (currentBalance > maxBalance) {
        maxBalance = currentBalance;
        maxLine = i + 1;
    }
}
console.log(`Max Balance: ${maxBalance} at line ${maxLine}`);
