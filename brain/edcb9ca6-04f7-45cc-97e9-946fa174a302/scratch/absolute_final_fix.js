
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Keep everything up to line 1651 (index 1650)
const newLines = lines.slice(0, 1652);

// Append the correct ending
newLines.push(
`    );
};

export default Settings;`
);

fs.writeFileSync(path, newLines.join('\n'));
