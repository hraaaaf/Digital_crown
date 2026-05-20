
const fs = require('fs');
const f = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');
let in_s = false;
let in_d = false;
let in_t = false;
let escaped = false;
for (let i = 0; i < f.length; i++) {
  const c = f[i];
  if (escaped) {
    escaped = false;
    continue;
  }
  if (c === '\\') {
    escaped = true;
    continue;
  }
  if (c === '\'' && !in_d && !in_t) in_s = !in_s;
  if (c === '\"' && !in_s && !in_t) in_d = !in_d;
  if (c === '`' && !in_s && !in_d) in_t = !in_t;
}
console.log('S:', in_s, 'D:', in_d, 'T:', in_t);
