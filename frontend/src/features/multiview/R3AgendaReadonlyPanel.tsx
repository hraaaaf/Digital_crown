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
  return <section data-testid="r3-real-agenda" aria-label="Agenda Cabinet lecture seule"
    className="min-w-0 space-y-2 p-3 text-text-main">
    <div className="flex items-center justify-between gap-2">
      <h3 className="text-sm font-semibold">Agenda</h3>
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
          : projected.length===0
            ? <p role="status" className="text-xs text-text-muted">Aucun rendez-vous aujourd'hui.</p>
            : <div className="max-h-[390px] overflow-auto">
                <table className="w-full text-left text-xs">
                  <caption className="sr-only">Rendez-vous vérifiés du jour, lecture seule</caption>
                  <thead><tr className="text-text-muted">
                    <th scope="col" className="py-2">Heure</th>
                    <th scope="col" className="py-2">Rendez-vous</th>
                    <th scope="col" className="py-2">Statut</th>
                  </tr></thead>
                  <tbody>{projected.map(item=><tr key={item.id} className="border-t border-border-main">
                    <td className="py-2 tabular-nums">{item.time}</td>
                    <td className="py-2">{item.patientLabel}</td>
                    <td className="py-2">{item.status}</td>
                  </tr>)}</tbody>
                </table>
              </div>}
  </section>;
}
