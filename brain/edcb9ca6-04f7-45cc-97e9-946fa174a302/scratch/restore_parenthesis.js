
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Fix IA tab missing )}
// It should be after the divs at L1615-1618.
// Let's find L1618 (0-indexed 1617)
if (lines[1617].includes('</div>')) {
    lines[1618] = "          )}";
}

fs.writeFileSync(path, lines.join('\n'));
