from pathlib import Path


def replace(path_str: str, pairs: list[tuple[str, str]]) -> None:
    path = Path(path_str)
    text = path.read_text(encoding='utf-8')
    before = text
    for old, new in pairs:
        text = text.replace(old, new)
    if text != before:
        path.write_text(text, encoding='utf-8')
        print(f'updated {path_str}')


banner = '''        {/* Bientôt disponible */}
        <div className="px-4 py-2 bg-amber-50 border border-amber-200 rounded-xl text-xs font-bold text-amber-700 flex items-center gap-2">
          <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 border border-amber-500/20">Bientôt</span>
          Module disponible. Les fonctions affichées sont celles actuellement prises en charge.
        </div>

'''
replace('frontend/src/pages/StockPage.tsx', [(banner, '')])
replace('frontend/src/pages/WaitingRoomPage.tsx', [(banner, '')])

replace('frontend/src/components/CrownBot/CrownBotChat.tsx', [
    ('Conversations LLM illimitées', 'Conversations avec l’assistant'),
    ('Actions avancées (ordonnances, devis auto)', 'Actions avancées (ordonnances et devis)'),
    ('Mémoire contextuelle V2', 'Mémoire contextuelle'),
    ('Conscience Proactive', 'Suivi contextuel'),
    ("Limite de l'assistant IA atteinte", "Limite de l’assistant atteinte"),
    ('3 échanges IA', '3 échanges'),
    ('préférences IA', 'préférences de l’assistant'),
    ('votre assistant IA', 'votre assistant'),
    ('<span className="ml-1.5 text-[8px] font-black bg-amber-400 text-slate-900 px-1.5 py-0.5 rounded-full uppercase tracking-wide">Bientôt</span>', ''),
    ('<span className="absolute -top-2 -right-2 bg-amber-400 text-slate-900 text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-wide shadow-md">\n              Bientôt\n            </span>', ''),
    ('Chat IA — Bientôt disponible', 'Assistant conversationnel'),
    ('Le chat conversationnel avec Crown Bot sera disponible dans la prochaine version.', 'Cette fonction n’est pas accessible depuis cet écran.'),
    ('Crown Bot V2 — En développement', 'Assistant Digital Crown'),
])

replace('frontend/src/features/admin/TeamManager.tsx', [
    ('Examen Clinique & IA', 'Examen clinique & assistance'),
    ('Diagnostic, plan de traitement, synthèses IA', 'Examen, plan de traitement et synthèses cliniques'),
])

replace('frontend/src/features/ortho/components/Step3Clinical.tsx', [
    ('Classe squelettique · legacy hors R11', 'Classe squelettique · donnée historique'),
])

replace('frontend/src/features/agenda/AgendaStudio.tsx', [
    ('Nouvelle demande RDV frontdesk', 'Nouvelle demande de rendez-vous'),
])
