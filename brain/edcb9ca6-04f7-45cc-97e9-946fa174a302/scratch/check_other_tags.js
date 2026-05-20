
import fs from 'fs';

const content = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');

const tags = ['button', 'label', 'span', 'h1', 'h2', 'h3', 'h4', 'p', 'input', 'select', 'textarea'];

tags.forEach(tag => {
    const open = (content.match(new RegExp(`<${tag}(?!\\w)`, 'g')) || []).length;
    const close = (content.match(new RegExp(`</${tag}>`, 'g')) || []).length;
    const selfClose = (content.match(new RegExp(`<${tag}[^>]*/>`, 'g')) || []).length;
    
    console.log(`${tag}: Open ${open}, Close ${close}, SelfClose ${selfClose}, Balance ${open - close - selfClose}`);
});
