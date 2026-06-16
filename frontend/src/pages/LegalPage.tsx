import { Link } from 'react-router-dom';
import Logo from '../assets/logo.png';

const legalContent = {
  terms: {
    title: 'Conditions Generales d Utilisation',
    updated: 'Derniere mise a jour : 16 juin 2026',
    sections: [
      {
        title: 'Objet',
        body: 'Digital Crown est une application de gestion de cabinet dentaire destinee aux professionnels de sante autorises. L acces est soumis a validation du compte et a licence active.',
      },
      {
        title: 'Responsabilite medicale',
        body: 'Les fonctionnalites d aide, d analyse et de generation documentaire ne remplacent pas le jugement clinique du praticien. Le praticien reste responsable des diagnostics, prescriptions, actes et documents remis au patient.',
      },
      {
        title: 'Compte et securite',
        body: 'L utilisateur doit conserver ses identifiants confidentiels, utiliser des mots de passe robustes et limiter les acces aux personnes habilitees du cabinet.',
      },
      {
        title: 'Licence',
        body: 'L utilisation en production necessite une licence active. En cas d expiration, certaines actions peuvent etre limitees en lecture seule jusqu a regularisation.',
      },
      {
        title: 'Support',
        body: 'Pour toute demande contractuelle, technique ou administrative, contactez le support Digital Crown aux coordonnees fournies par SANINOVA.',
      },
    ],
  },
  privacy: {
    title: 'Politique de Confidentialite',
    updated: 'Derniere mise a jour : 16 juin 2026',
    sections: [
      {
        title: 'Donnees traitees',
        body: 'Digital Crown traite des donnees de compte, de cabinet, de patients, de rendez-vous, de documents medicaux et de traces d audit necessaires au fonctionnement du service.',
      },
      {
        title: 'Finalites',
        body: 'Les donnees sont utilisees pour fournir l application, securiser les acces, produire les documents du cabinet, conserver l historique et assurer la maintenance.',
      },
      {
        title: 'Confidentialite medicale',
        body: 'Les donnees de sante doivent etre saisies uniquement par des professionnels habilites. L acces est limite aux comptes autorises du cabinet et aux operations techniques strictement necessaires.',
      },
      {
        title: 'Conservation',
        body: 'Les donnees sont conservees pendant la duree necessaire au service, aux obligations professionnelles et aux exigences legales applicables.',
      },
      {
        title: 'Droits',
        body: 'Selon la reglementation applicable, les personnes concernees peuvent demander l acces, la rectification, la limitation ou la suppression des donnees lorsque cela est legalement possible.',
      },
    ],
  },
} as const;

export const LegalPage = ({ type }: { type: keyof typeof legalContent }) => {
  const content = legalContent[type];

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900">
      <div className="mx-auto max-w-3xl">
        <Link to="/login" className="mb-8 inline-flex items-center gap-3">
          <img src={Logo} alt="Digital Crown" className="h-10 w-auto" />
          <span className="text-sm font-bold text-slate-600">Retour</span>
        </Link>

        <article className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Digital Crown</p>
          <h1 className="mt-3 text-3xl font-black text-slate-950">{content.title}</h1>
          <p className="mt-2 text-sm font-semibold text-slate-500">{content.updated}</p>

          <div className="mt-8 space-y-7">
            {content.sections.map((section) => (
              <section key={section.title}>
                <h2 className="text-base font-black text-slate-900">{section.title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">{section.body}</p>
              </section>
            ))}
          </div>

          <p className="mt-8 rounded-xl bg-slate-50 p-4 text-xs font-semibold leading-5 text-slate-500">
            Ce texte est un socle operationnel pour l app. Il doit etre valide et adapte par un conseil juridique avant
            lancement commercial public.
          </p>
        </article>
      </div>
    </main>
  );
};
