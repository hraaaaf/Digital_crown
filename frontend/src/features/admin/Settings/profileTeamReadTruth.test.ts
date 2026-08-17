import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const settingsDir = resolve(process.cwd(), 'src/features/admin/Settings');
const containerSource = readFileSync(resolve(settingsDir, 'SettingsContainer.tsx'), 'utf8');
const teamGateSource = readFileSync(resolve(settingsDir, 'components/TeamReadTruthGate.tsx'), 'utf8');

describe('Settings profile/team read truth', () => {
  it('blocks profile-backed settings and global save after a failed profile read', () => {
    expect(containerSource).toContain("method === 'get' && url === '/clinics/me'");
    expect(containerSource).toContain('setProfileReadError(true)');
    expect(containerSource).toContain("const profileBackedTabs: Tab[] = ['profil', 'branding', 'ia']");
    expect(containerSource).toContain('access.canSettings && !profileReadError');
    expect(containerSource).toContain("'Profil indisponible'");
    expect(containerSource).toContain('Aucune valeur de repli n’est modifiable');
  });

  it('does not expose team management until both members and quota reads are verified', () => {
    expect(containerSource).toContain('<TeamReadTruthGate />');
    expect(teamGateSource).toContain('Promise.all([');
    expect(teamGateSource).toContain("api.get(`/team/?_truth=${Date.now()}`)");
    expect(teamGateSource).toContain("api.get('/team/quota')");
    expect(teamGateSource).toContain("setReadState('error')");
    expect(teamGateSource).toContain('Équipe indisponible');
    expect(teamGateSource).toContain('Aucune gestion d’équipe n’est disponible');
    expect(teamGateSource).toContain("return <TeamManager />");
  });
});
