
import fs from 'fs';

const content = fs.readFileSync('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx', 'utf8');

let openTags = 0;
let closeTags = 0;

// Simple regex to count <div> and </div>
// This is not perfect but will give a rough idea
const divOpen = content.match(/<div/g) || [];
const divClose = content.match(/<\/div>/g) || [];

console.log('Open <div>:', divOpen.length);
console.log('Close </div>:', divClose.length);

// Let's try to find where the balance breaks
const lines = content.split('\n');
let currentBalance = 0;
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const opens = (line.match(/<div/g) || []).length;
    const closes = (line.match(/<\/div>/g) || []).length;
    currentBalance += (opens - closes);
    if (currentBalance < 0) {
        console.log(`Balance broke at line ${i + 1}: ${currentBalance}`);
        // Reset to 0 to keep tracing?
        // currentBalance = 0;
    }
}
console.log('Final Balance:', currentBalance);
