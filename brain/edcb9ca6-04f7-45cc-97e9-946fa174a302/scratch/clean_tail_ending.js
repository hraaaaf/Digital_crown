
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Remove the last 10 lines and replace with a clean ending
const newLines = lines.slice(0, lines.length - 10);

newLines.push(
`    );
};

export default Settings;`
);

fs.writeFileSync(path, newLines.join('\n'));
