/**
 * Parseur de fichiers .ics (iCalendar) pour l'import Google Agenda
 */

export interface ParsedEvent {
  patient_name: string;
  datetime_start: string;
  duration_minutes: number;
  notes: string;
}

/**
 * Fonction rudimentaire pour parser une date ICS (ex: 20260510T090000Z)
 * en un objet Date valide JS.
 */
const parseIcsDate = (icsDate: string): Date | null => {
  if (!icsDate) return null;
  // Format standard: YYYYMMDDTHHMMSSZ
  const match = icsDate.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})(Z)?$/);
  if (match) {
    const [_, y, m, d, h, min, s, z] = match;
    const dateStr = `${y}-${m}-${d}T${h}:${min}:${s}${z ? 'Z' : ''}`;
    return new Date(dateStr);
  }
  return null;
};

/**
 * Parse le contenu brut d'un fichier .ics et retourne un tableau d'événements
 */
export const parseIcsContent = (content: string): ParsedEvent[] => {
  const events: ParsedEvent[] = [];
  const lines = content.split(/\r?\n/);
  
  let currentEvent: any = null;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    if (line === 'BEGIN:VEVENT') {
      currentEvent = {};
    } else if (line === 'END:VEVENT') {
      if (currentEvent && currentEvent.dtstart && currentEvent.summary) {
        
        // Calcul de la durée
        let durationMinutes = 30; // Par défaut
        if (currentEvent.dtstart && currentEvent.dtend) {
            const start = parseIcsDate(currentEvent.dtstart);
            const end = parseIcsDate(currentEvent.dtend);
            if (start && end) {
                durationMinutes = Math.round((end.getTime() - start.getTime()) / 60000);
            }
        }
        
        // Nettoyage basique du titre pour extraire le nom (ex: "Consultation Dupont" -> "Dupont")
        // On garde le summary complet pour l'instant
        const summary = currentEvent.summary.replace(/\\,/g, ',').replace(/\\;/g, ';');
        const description = currentEvent.description ? currentEvent.description.replace(/\\n/g, '\n') : '';

        // Si la durée est négative ou absurde, on ignore (erreurs de parsing date)
        if (durationMinutes > 0 && durationMinutes < 1440) {
            events.push({
                patient_name: summary,
                datetime_start: parseIcsDate(currentEvent.dtstart)?.toISOString() || new Date().toISOString(),
                duration_minutes: durationMinutes,
                notes: description,
            });
        }
      }
      currentEvent = null;
    } else if (currentEvent) {
      // Les lignes ICS peuvent être cassées (folded), on suppose ici un format simple.
      // Dans la réalité, il faudrait un parseur robuste gérant le folding.
      if (line.startsWith('DTSTART:')) currentEvent.dtstart = line.substring(8);
      else if (line.startsWith('DTSTART;VALUE=DATE:')) currentEvent.dtstart = line.substring(19) + 'T000000Z'; // Evènement journée entière
      else if (line.startsWith('DTSTART;')) currentEvent.dtstart = line.split(':')[1];
      
      else if (line.startsWith('DTEND:')) currentEvent.dtend = line.substring(6);
      else if (line.startsWith('DTEND;VALUE=DATE:')) currentEvent.dtend = line.substring(17) + 'T000000Z';
      else if (line.startsWith('DTEND;')) currentEvent.dtend = line.split(':')[1];
      
      else if (line.startsWith('SUMMARY:')) currentEvent.summary = line.substring(8);
      else if (line.startsWith('DESCRIPTION:')) currentEvent.description = line.substring(12);
    }
  }
  
  return events;
};
