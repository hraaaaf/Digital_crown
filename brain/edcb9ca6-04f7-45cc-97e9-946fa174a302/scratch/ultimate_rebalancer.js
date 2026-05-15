
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
let f = fs.readFileSync(path, 'utf8');

const count = (str, char) => (str.match(new RegExp('\\' + char, 'g')) || []).length;
const countDivs = (str) => (str.match(/<div(?![^>]*\/>)/g) || []).length;
const countDivClosures = (str) => (str.match(/<\/div>/g) || []).length;

let b_brace = count(f, '{') - count(f, '}');
let b_paren = count(f, '(') - count(f, ')');
let b_div = countDivs(f) - countDivClosures(f);

console.log('Initial Balances - Braces:', b_brace, 'Parens:', b_paren, 'Divs:', b_div);

const lines = f.split(/\r?\n/);

// Remove closures from the end if balance is negative
while (b_brace < 0 && lines[lines.length-1].trim() === '};') { lines.pop(); b_brace++; }
while (b_paren < 0 && lines[lines.length-1].trim() === ');') { lines.pop(); b_paren++; }
while (b_div < 0 && lines[lines.length-1].trim() === '</div>') { lines.pop(); b_div++; }

let suffix = '';
if (b_div > 0) suffix += '</div>\n'.repeat(b_div);
if (b_paren > 0) suffix += ');\n'.repeat(b_paren);
if (b_brace > 0) suffix += '};\n'.repeat(b_brace);

// Clean up existing exports
const cleanLines = lines.filter(l => !l.trim().includes('export default Settings'));

fs.writeFileSync(path, cleanLines.join('\n').trim() + '\n' + suffix + '\nexport default Settings;');
