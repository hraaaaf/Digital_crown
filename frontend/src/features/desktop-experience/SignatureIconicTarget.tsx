import { useState } from 'react';
import {
  Activity, CalendarDays, ChevronRight, CircleUserRound, Eye,
  Image as ImageIcon, LayoutDashboard, LockKeyhole, Sparkles,
} from 'lucide-react';
import './SignatureIconicTarget.css';

type ExperiencePreview = 'core' | 'iconic';
type WorkspacePreview = 'dashboard' | 'agenda' | 'dossier' | 'imagerie';

const SURFACES: ReadonlyArray<{
  id: WorkspacePreview;
  title: string;
  description: string;
  Icon: typeof LayoutDashboard;
}> = [
  {
    id: 'dashboard', title: 'Tableau de bord',
    description: 'Organisation du cabinet et raccourcis autorisés',
    Icon: LayoutDashboard,
  },
  {
    id: 'agenda', title: 'Agenda',
    description: 'Planification du cabinet — aucun rendez-vous simulé',
    Icon: CalendarDays,
  },
  {
    id: 'dossier', title: 'Dossier patient',
    description: 'Le contexte patient et les autorisations restent inchangés',
    Icon: CircleUserRound,
  },
  {
    id: 'imagerie', title: 'Imagerie',
    description: 'Médiathèque et comparaison clinique existantes',
    Icon: ImageIcon,
  },
];

/**
 * LOT07 / 07-B G2 TARGET-only visual proof.
 *
 * Intentional NON-PRODUCTION DEMONSTRATOR. No real patient payload, routing,
 * permission grants, settings mutation or persistence. Neither this control
 * nor its surface selection activates an experience in the Cabinet app.
 * Iconic is a visual layer, not a new clinical workflow or a cabinet theme.
 */
export function SignatureIconicTarget() {
  const [preview, setPreview] = useState<ExperiencePreview>('core');
  const [workspace, setWorkspace] = useState<WorkspacePreview>('dashboard');
  const active = SURFACES.find(surface => surface.id === workspace) ?? SURFACES[0];
  const ActiveIcon = active.Icon;
  const iconic = preview === 'iconic';

  return (
    <section
      className="dc07-iconic-target"
      data-v15-07-g2-target
      data-preview-experience={preview}
      aria-label="Laboratoire visuel Signature Core et Iconic"
    >
      <header className="dc07-iconic-target__intro">
        <div>
          <p className="dc07-iconic-target__eyebrow">Digital Crown · LOT07 / 07-B</p>
          <h2>Signature Iconic — cible visuelle</h2>
          <p>Comparaison réversible du style. Aucune donnée clinique, aucune préférence enregistrée.</p>
        </div>
        <span className="dc07-iconic-target__lab" aria-label="Aperçu non clinique">
          <LockKeyhole size={14} aria-hidden="true" /> Maquette non clinique
        </span>
      </header>

      <div className="dc07-iconic-target__controls" role="group" aria-label="Style à prévisualiser">
        <button
          type="button"
          aria-pressed={!iconic}
          onClick={() => setPreview('core')}
          className="dc07-iconic-target__choice"
        >
          <Eye size={16} aria-hidden="true" /> Signature Core
        </button>
        <button
          type="button"
          aria-pressed={iconic}
          onClick={() => setPreview('iconic')}
          className="dc07-iconic-target__choice"
        >
          <Sparkles size={16} aria-hidden="true" /> Signature Iconic
        </button>
      </div>

      <div className="dc07-iconic-target__shell">
        <aside aria-label="Navigation de démonstration" className="dc07-iconic-target__rail">
          <div className="dc07-iconic-target__brand">
            <span className="dc07-iconic-target__emblem"><Activity size={20} aria-hidden="true" /></span>
            <span>Digital Crown <small>Signature</small></span>
          </div>
          <nav aria-label="Écrans témoins">
            {SURFACES.map(({ id, title, Icon }) => (
              <button
                key={id}
                type="button"
                className="dc07-iconic-target__nav"
                aria-current={workspace === id ? 'page' : undefined}
                onClick={() => setWorkspace(id)}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{title}</span>
                {iconic && workspace === id && <ChevronRight size={15} aria-hidden="true" />}
              </button>
            ))}
          </nav>
          <p className="dc07-iconic-target__rail-foot">Aucun patient chargé</p>
        </aside>

        <main className="dc07-iconic-target__body">
          <div className="dc07-iconic-target__section-top">
            <div>
              <p className="dc07-iconic-target__eyebrow">Espace de travail · Démonstration</p>
              <h3><ActiveIcon size={24} aria-hidden="true" /> {active.title}</h3>
              <p>{active.description}</p>
            </div>
            <span className="dc07-iconic-target__marker">
              {iconic && <Sparkles size={14} aria-hidden="true" />}
              {iconic ? 'Style Iconic' : 'Style Core'}
            </span>
          </div>
          <div className="dc07-iconic-target__cards" aria-label="Structure de page témoin">
            <article className="dc07-iconic-target__card">
              <span className="dc07-iconic-target__card-glyph"><ActiveIcon size={22} aria-hidden="true" /></span>
              <h4>Fonctionnalités conservées</h4>
              <p>Les règles métier, les permissions et les actions cliniques ne sont pas modifiées par un style.</p>
            </article>
            <article className="dc07-iconic-target__card">
              <span className="dc07-iconic-target__card-glyph"><LockKeyhole size={22} aria-hidden="true" /></span>
              <h4>Contexte protégé</h4>
              <p>Le dossier actif reste unique, et toutes les opérations continuent d'utiliser les contrôles existants.</p>
            </article>
          </div>
          <p className="dc07-iconic-target__footnote" role="status">
            Aperçu seulement : ce changement ne sauvegarde ni palette cabinet ni choix utilisateur/poste.
          </p>
        </main>
      </div>
    </section>
  );
}
