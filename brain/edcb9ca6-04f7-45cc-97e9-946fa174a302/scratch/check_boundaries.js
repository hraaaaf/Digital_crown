
import fs from 'fs';

const content = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');
const lines = content.split('\n');

let balance = 0;
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
    const closes = (line.match(/<\/div>/g) || []).length;
    balance += (opens - closes);
    
    // Check at specific points
    if (i + 1 === 542) console.log(`Balance before Profil: ${balance}`);
    if (i + 1 === 1173) console.log(`Balance after Profil: ${balance}`);
    if (i + 1 === 1174) console.log(`Balance before Branding: ${balance}`);
    if (i + 1 === 1533) console.log(`Balance after Branding: ${balance}`);
    if (i + 1 === 1534) console.log(`Balance before IA: ${balance}`);
    if (i + 1 === 1614) console.log(`Balance after IA: ${balance}`);
    if (i + 1 === 1616) console.log(`Balance before Securite: ${balance}`);
    if (i + 1 === 1640) console.log(`Balance after Securite: ${balance}`);
    if (i + 1 === 1642) console.log(`Balance before Equipe: ${balance}`);
    if (i + 1 === 1646) console.log(`Balance after Equipe: ${balance}`);
}
console.log(`Final balance: ${balance}`);
