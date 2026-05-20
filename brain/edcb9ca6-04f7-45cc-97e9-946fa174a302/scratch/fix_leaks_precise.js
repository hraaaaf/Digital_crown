
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
let content = fs.readFileSync(path, 'utf8');

// Fix Branding Tab End
const brandingSearch = /                <\/div>\r?\n              <\/div>\r?\n \r?\n            <\/div>\r?\n          <\/div>\r?\n        <\/div>\r?\n      \)}/g;
const brandingReplace = `                </div>
              </div>
            </div>
          )}`

// Fix IA Tab End
const iaSearch = /            <\/div>\r?\n          <\/div>\r?\n        <\/div>\r?\n      \)}/g;
const iaReplace = `            </div>
          </div>
        </div>
      )}`

// Actually, I'll just do a very targeted replace using line numbers and substrings to avoid regex pitfalls with whitespace.
const lines = content.split('\n');

// Branding fix (Lines 1524-1530)
// We want exactly 3 divs and one )}
lines[1523] = "                  </div>";
lines[1524] = "                </div>";
lines[1525] = "              </div>";
lines[1526] = "            </div>";
lines[1527] = "          )}";
lines[1528] = "";
lines[1529] = "";

// IA fix (Lines 1610-1613)
// It opens 2 divs (1535, 1541). Needs 2 closures.
lines[1609] = "            </div>";
lines[1610] = "          </div>";
lines[1611] = "        )}";
lines[1612] = "";

fs.writeFileSync(path, lines.join('\n'));
