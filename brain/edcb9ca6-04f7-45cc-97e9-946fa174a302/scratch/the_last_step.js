
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Add 2 divs before the end
const lastIndex = lines.length - 4; // index of );
lines.splice(lastIndex, 0, "        </div>", "      </div>");

fs.writeFileSync(path, lines.join('\n'));
