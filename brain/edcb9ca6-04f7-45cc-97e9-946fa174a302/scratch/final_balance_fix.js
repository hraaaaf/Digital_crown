
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split('\n');

// Branding fix (Lines 1528-1532 roughly)
// Target:
// L1528: 
// L1529:             </div>
// L1530:           </div>
// L1531:         </div>
// L1532:       )}

// Based on my cat output:
// line 1528 is the empty one.
lines[1527] = "      )}";
lines[1528] = "";
lines[1529] = "";
lines[1530] = "";
lines[1531] = ""; // Extra safety

// IA fix (Lines 1614-1617 roughly)
// Audit said it leaked 3 divs.
// It ends around 1613.
// L1611:             </div>
// L1612:           </div>
// L1613:         </div>
// L1614:       )}

// We want it to end at 4.
// Let's check IA start again.
// L1535: O1
// L1541: O2
// So it needs 2 closures. 
// It currently has 3 closures (L1611, 1612, 1613).
// So remove ONE closure.

lines[1612] = "      )}";
lines[1613] = "";

fs.writeFileSync(path, lines.join('\n'));
