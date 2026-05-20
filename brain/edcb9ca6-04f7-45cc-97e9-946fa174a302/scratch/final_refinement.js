
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Fix L1647-1650
lines[1647] = "                </div>";
lines[1648] = "              )}";
lines[1649] = "            </div>";
lines[1650] = "          </div>";
lines[1651] = "        </div>";
lines[1652] = "      </div>";
lines.splice(1653, 0, "    );");
lines.splice(1654, 0, "};");

fs.writeFileSync(path, lines.join('\n'));
