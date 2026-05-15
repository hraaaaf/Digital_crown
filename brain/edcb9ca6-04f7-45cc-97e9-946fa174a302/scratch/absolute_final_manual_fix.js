
import fs from 'fs';

const path = 'c:/Users/lenovo/Documents/Cabinet/DigitalCrown/frontend/src/pages/Settings.tsx';
const content = fs.readFileSync(path, 'utf8');
const lines = content.split(/\r?\n/);

// Everything before TAB 5 (around L1642, index 1641)
const newLines = lines.slice(0, 1641);

newLines.push(
`              {/* TAB 5 : MON ÉQUIPE */}
              {activeTab === 'equipe' && (
                <div className="animate-in slide-in-from-right-4 duration-500">
                  <TeamManager />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
};

export default Settings;`
);

fs.writeFileSync(path, newLines.join('\n'));
