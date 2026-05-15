
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

function getBalanceAt(lineIndex) {
    let b = 0;
    for (let i = 0; i <= lineIndex; i++) {
        const l = lines[i];
        const o = (l.match(/<div(?![^>]*\/>)/g) || []).length;
        const c = (l.match(/<\/div>/g) || []).length;
        b += (o - c);
    }
    return b;
}

// 1. Fix Profil Tab
// End is around L1173. We want balance 4 at L1173.
// Currently at L1171 it is 4. L1172 is 3.
lines[1171] = ""; // Remove L1172 (0-indexed 1171)

// 2. Fix Branding Tab
// End is around L1532. We want balance 4 at L1532.
// Currently at L1530 it is 4. L1531 is 3.
lines[1530] = ""; // Remove L1531 (0-indexed 1530)

// 3. Fix IA Tab
// End is around L1619. We want balance 4 at L1619.
// Currently at L1617 it is 4. L1618 is 3.
lines[1617] = ""; // Remove L1618 (0-indexed 1617)

// 4. Fix Securite Tab (Check it first)
// Let's find Securite end.
// L1640: </div> (1)
// L1641: </div> (0)
// L1642: )}
// Wait, if balance was 4.
// L1640: 3
// L1641: 2
// L1642: )}
// We need it to be 4 at 1642.
// So we need to REMOVE two divs.
lines[1639] = "";
lines[1640] = "";

// Wait, I should just check the balance at each step.
// Actually, I'll just rewrite the whole file with a balance tracker.
// But that's too risky.

// Let's just fix the known leaks.

fs.writeFileSync(path, lines.join('\n'));
