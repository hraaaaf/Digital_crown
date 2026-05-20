
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Fix the final closures
// Current L1650-1652:
// 1650:         </div>
// 1651:       </div>
// 1652:     );

// Change to:
// 1650:             </div>
// 1651:           </div>
// 1652:         </div>
// 1653:       </div>
// 1654:     );

lines[1649] = "            </div>";
lines[1650] = "          </div>";
lines[1651] = "        </div>";
lines[1652] = "      </div>";
lines.splice(1653, 0, "    );");

fs.writeFileSync(path, lines.join('\n'));
