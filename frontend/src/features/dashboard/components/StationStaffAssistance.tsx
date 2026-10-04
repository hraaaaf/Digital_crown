import { useCallback, useEffect, useState } from 'react';
import { BellRing, Check } from 'lucide-react';
import {
  stationStaffAssistanceService,
  type StationStaffAssistanceAlert,
} from '../../../services/stationStaffAssistance';

export const StationStaffAssistance = ({ visible }: { visible: boolean }) => {
  const [alerts, setAlerts] = useState<StationStaffAssistanceAlert[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    if (!visible) return;
    try {
      setAlerts(await stationStaffAssistanceService.list());
    } catch {
      // Fail closed visually: do not invent an alert when the staff feed is unavailable.
    }
  }, [visible]);

  useEffect(() => {
    if (!visible) {
      setAlerts([]);
      return undefined;
    }
    void refresh();
    const timer = window.setInterval(() => void refresh(), 15000);
    return () => window.clearInterval(timer);
  }, [refresh, visible]);

  const acknowledge = async (alertId: number) => {
    setBusyId(alertId);
    try {
      await stationStaffAssistanceService.acknowledge(alertId);
      setAlerts((current) => current.filter((item) => item.alertId !== alertId));
    } finally {
      setBusyId(null);
    }
  };

  if (!visible || alerts.length === 0) return null;

  return (
    <section data-station-staff-assistance role="status" className="rounded-elite-lg border border-amber-200 bg-amber-50 p-5 shadow-elite">
      <div className="flex items-start gap-3">
        <BellRing className="mt-0.5 shrink-0 text-amber-700" size={22} aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <h2 className="font-black text-amber-950">Assistance demandée à la station</h2>
          <p className="mt-1 text-sm font-semibold text-amber-800">
            {alerts.length === 1 ? 'Une personne identifiée' : `${alerts.length} personnes identifiées`} n’a pas de rendez-vous retrouvé aujourd’hui.
          </p>
          <div className="mt-4 grid gap-2">
            {alerts.map((alert) => (
              <div key={alert.alertId} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-white/80 px-4 py-3">
                <span className="text-sm font-bold text-amber-950">Station · demande #{alert.alertId}</span>
                <button
                  type="button"
                  disabled={busyId === alert.alertId}
                  onClick={() => void acknowledge(alert.alertId)}
                  className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-amber-900 px-4 text-sm font-black text-white disabled:opacity-50"
                >
                  <Check size={16} aria-hidden="true" />
                  {busyId === alert.alertId ? 'Acquittement…' : 'Pris en charge'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
