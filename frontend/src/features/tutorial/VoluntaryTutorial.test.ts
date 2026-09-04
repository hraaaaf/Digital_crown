import fs from 'node:fs';
import path from 'node:path';
import { beforeEach, describe, expect, it } from 'vitest';
import { useVoluntaryTutorial } from './VoluntaryTutorial';

const tutorialPath = path.resolve(__dirname, 'VoluntaryTutorial.tsx');
const headerPath = path.resolve(__dirname, '../../components/Header.tsx');
const layoutPath = path.resolve(__dirname, '../../components/Layout/MainLayout.tsx');
const quickActionsPath = path.resolve(__dirname, '../dashboard/components/QuickActions.tsx');

const tutorialSource = fs.readFileSync(tutorialPath, 'utf8');
const headerSource = fs.readFileSync(headerPath, 'utf8');
const layoutSource = fs.readFileSync(layoutPath, 'utf8');
const quickActionsSource = fs.readFileSync(quickActionsPath, 'utf8');

describe('Voluntary contextual tutorial', () => {
  beforeEach(() => {
    useVoluntaryTutorial.setState({
      open: false,
      activeGuide: null,
      step: 0,
      progress: {},
    });
  });

  it('is closed by default and only opens through an explicit action', () => {
    expect(useVoluntaryTutorial.getState().open).toBe(false);
    useVoluntaryTutorial.getState().openPanel();
    expect(useVoluntaryTutorial.getState().open).toBe(true);
    useVoluntaryTutorial.getState().closePanel();
    expect(useVoluntaryTutorial.getState().open).toBe(false);
  });

  it('pauses without forcing a later reopen', () => {
    useVoluntaryTutorial.getState().startGuide('agenda');
    expect(useVoluntaryTutorial.getState().open).toBe(true);
    useVoluntaryTutorial.getState().pause();
    expect(useVoluntaryTutorial.getState().open).toBe(false);
    expect(useVoluntaryTutorial.getState().activeGuide).toBeNull();
    expect(useVoluntaryTutorial.getState().progress.agenda?.status).toBe('paused');
  });

  it('contains no timer or joyride auto-launch mechanism', () => {
    expect(tutorialSource).not.toContain('setTimeout(');
    expect(tutorialSource).not.toContain('setInterval(');
    expect(tutorialSource).not.toContain('react-joyride');
    expect(tutorialSource).toContain('open: false');
    expect(tutorialSource).toContain('progress: readProgress()');
  });

  it('mounts a global explicit help entry and non-blocking panel', () => {
    expect(headerSource).toContain('<TutorialHelpButton />');
    expect(layoutSource).toContain('<VoluntaryTutorialPanel />');
    expect(tutorialSource).toContain('aria-label="Ouvrir Aide et Guide"');
    expect(tutorialSource).toContain('Guide volontaire');
    expect(tutorialSource).toContain('Reprendre plus tard');
    expect(tutorialSource).not.toContain('fixed inset-0');
  });

  it('filters guides through existing permission policies', () => {
    expect(tutorialSource).toContain("hasAccess(user, 'patients')");
    expect(tutorialSource).toContain("hasAccess(user, 'agenda')");
    expect(tutorialSource).toContain('allowedDocumentStudioTabs(user)');
  });

  it('uses stable guide hooks for dashboard shortcuts', () => {
    expect(quickActionsSource).toContain('data-guide="quick-action-new-patient"');
    expect(quickActionsSource).toContain('data-guide="quick-action-agenda"');
  });
});
