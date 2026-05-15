
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Ensure the file ends correctly
const newLines = lines.filter(l => l.trim() !== 'export default Settings;');
newLines.push('    );');
newLines.push('};');
newLines.push('');
newLines.push('export default Settings;');

fs.writeFileSync(path, newLines.join('\n'));
