import type { AppUser } from '../../types';
import { useTodayAppointments } from '../dashboard/hooks/useTodayAppointments';
import { projectReadOnlyAppointments } from '../command/command-cabinet-readonly-policy';
import { hasAccess } from '../../utils/accessControl';

const noopRefresh = async ():Promise<void> => {};
const noopCompleted = ():void => {};

/** Same authenticated appointment source and privacy projection as Command Cabinet.
 * Display-only: no write handler is connected, no mutations, no fabricated events.
 */
export function R3AgendaReadonlyPanel({user}:{user:AppUser}) {
  const {appointments,appointmentsState,refreshAppointments} = useTodayAppointments({
    user,authLoading:false,onStatsRefresh:noopRefresh,onCompleted:noopCompleted,
  });
  const authorized=hasAccess(user,'agenda');
  const projected=authorized ? projectReadOnlyAppointments(appointments,hasAccess(user,'patients')) : null;
  const ready=appointmentsState==='ready' && projected!==null;
  const rows=projected ?? [];
  const agendaVisualState=!authorized?'denied':appointmentsState==='ready'
    ? (rows.length===0?'empty':'populated') : appointmentsState;
  return <section data-testid="r3-real-agenda" data-r3-agenda-state={agendaVisualState}
    aria-label="Agenda Cabinet lecture seule"
    className="min-w-0 space-y-2 p-3 text-text-main">
    <div className="flex items-center justify-between gap-2">
      <div className="flex min-w-0 items-center gap-2">
        <h3 className="text-sm font-semibold">Agenda</h3>
        {ready && <span className="rounded-full border border-border-main bg-medical-pearl px-2 py-0.5 text-[11px] font-semibold text-primary-ink">
          {rows.length} RDV
        </span>}
      </div>
      {authorized && <button type="button" onClick={()=>{void refreshAppointments();}}
        disabled={appointmentsState==='loading'}
        aria-label="Actualiser l'agenda"
        className="min-h-10 rounded-lg border border-border-main bg-card px-2 text-xs text-text-main disabled:opacity-50">Actualiser</button>}
    </div>
    {!authorized ? <p role="alert">Accès refusé.</p> :
      appointmentsState==='loading'||appointmentsState==='idle'
        ? <p role="status" className="text-xs text-text-muted">Chargement…</p>
        : !ready
          ? <p role="alert" className="text-xs">Agenda indisponible.</p>
          : rows.length===0
            ? <div data-testid="r3-agenda-empty" className="flex min-h-[120px] items-center justify-center rounded-xl border border-dashed border-border-main bg-medical-pearl/50 px-4 py-5 text-center">
                <p role="status" className="text-xs text-text-muted">Aucun rendez-vous aujourd'hui.</p>
              </div>
            : <div className="max-h-[390px] overflow-auto">
                <table className="w-full text-left text-xs">
                  <caption className="sr-only">Rendez-vous vérifiés du jour, lecture seule</caption>
                  <thead><tr className="text-text-muted">
                    <th scope="col" className="py-2">Heure</th>
                    <th scope="col" className="py-2">Rendez-vous</th>
                    <th scope="col" className="py-2">Statut</th>
                  </tr></thead>
                  <tbody>{rows.map(item=><tr key={item.id} className="border-t border-border-main">
                    <td className="py-2 tabular-nums">{item.time}</td>
                    <td className="py-2">{item.patientLabel}</td>
                    <td className="py-2">{item.status}</td>
                  </tr>)}</tbody>
                </table>
              </div>}
  </section>;
}
