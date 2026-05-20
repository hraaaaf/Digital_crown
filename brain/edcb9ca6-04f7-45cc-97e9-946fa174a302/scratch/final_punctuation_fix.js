
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Fix the very end
lines[1659] = "      </div>";
lines[1660] = "    );";
lines[1661] = "};";

fs.writeFileSync(path, lines.join('\n'));
