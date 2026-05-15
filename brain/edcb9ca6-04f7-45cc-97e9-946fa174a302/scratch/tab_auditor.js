
import fs from 'fs';

const content = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');
const lines = content.split(/\r?\n/);

const tabs = [
    { name: 'Profil', start: 543, end: 1173 },
    { name: 'Branding', start: 1177, end: 1532 },
    { name: 'IA', start: 1537, end: 1619 },
    { name: 'Securite', start: 1622, end: 1641 },
    { name: 'Equipe', start: 1645, end: 1649 }
];

tabs.forEach(tab => {
    let balance = 0;
    for (let i = tab.start - 1; i < tab.end; i++) {
        const line = lines[i] || "";
        const opens = (line.match(/<div(?![^>]*\/>)/g) || []).length;
        const closes = (line.match(/<\/div>/g) || []).length;
        balance += (opens - closes);
    }
    console.log(`Tab ${tab.name}: Balance Change ${balance}`);
});
