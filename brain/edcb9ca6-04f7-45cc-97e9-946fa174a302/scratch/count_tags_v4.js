
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
    
    if (i === 1170) console.log(`Balance after Profil: ${currentBalance}`);
    if (i === 1525) console.log(`Balance after Branding: ${currentBalance}`);
    if (i === 1608) console.log(`Balance after IA: ${currentBalance}`);
    if (i === 1635) console.log(`Balance after Securite: ${currentBalance}`);
    if (i === 1642) console.log(`Balance after Equipe: ${currentBalance}`);
}
console.log('Final Balance:', currentBalance);
