import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { hasAccess } from '../../utils/accessControl';
import { useAuthStore } from '../../stores/useAuthStore';
import {
  fetchOrthoCase, fetchOrthoLongitudinalCompare, fetchOrthoTimepoints,
  type OrthoLongitudinalCompare,
} from './orthoLongitudinalCompare';
import { gateR6ThreeTimepoints, type R6Trajectory } from './r6ThreeTimepoints';
import { normalizeR6PresenterUserId, projectR6Presenter, R6PresenterWindow } from './r6PatientPresenter';

type Props = {
  patientId: number;
  caseId: number;
  userId: string | null;
  allowed: boolean;
  trajectory: R6Trajectory | null;
  comparison: OrthoLongitudinalCompare | undefined;
  fromOrdinal: number | null;
  toOrdinal: number | null;
};

/**
 * R6/07.1.D DEV-only explicit opt-in; parent owns all auth and API requests.
 * A disconnected/foreign/invalid data source NEVER creates an output window.
 */
export const R6PatientPresenterControl = ({
  patientId,caseId,userId,allowed,trajectory,comparison,fromOrdinal,toOrdinal,
}: Props) => {
  const presenter=useRef<R6PresenterWindow | null>(null);
  const epoch=useRef(0);
  const [opened,setOpened]=useState(false);
  const [blocked,setBlocked]=useState(false);
  const snapshot=useMemo(()=>allowed
    ? projectR6Presenter(trajectory,comparison,userId,fromOrdinal,toOrdinal)
    : null,
  [allowed,trajectory,comparison,userId,fromOrdinal,toOrdinal]);

  const close=useCallback(()=>{
    epoch.current++;
    presenter.current?.close();
    presenter.current=null;
    setOpened(false);
  },[]);

  // Closing a patient tab or changing account/case must immediately blank
  // the separate display even if the new patient's query is still pending.
  useEffect(()=>()=>close(),[close,patientId,caseId,userId]);

  useEffect(()=>{
    if (!snapshot || !allowed) {close(); return;}
    if (presenter.current && !presenter.current.update(snapshot)) close();
  },[snapshot,allowed,close]);

  useEffect(()=>{
    if (!opened || !snapshot || !allowed) return;
    const serial=++epoch.current;
    const verify=async()=>{
      const auth=useAuthStore.getState();
      if (!auth.isAuthenticated || normalizeR6PresenterUserId(auth.user?.id)!==userId ||
          !hasAccess(auth.user,'patients') || !hasAccess(auth.user,'clinical')) {
        if(serial===epoch.current)close();
        return;
      }
      try {
        const [verifiedCase,points]=await Promise.all([
          fetchOrthoCase(patientId),
          fetchOrthoTimepoints(patientId,caseId),
        ]);
        if(serial!==epoch.current)return;
        const fresh=gateR6ThreeTimepoints(patientId,caseId,
          verifiedCase?.id===caseId && verifiedCase.patient_id===patientId?points:null);
        if(!fresh.ok || !trajectory ||
            JSON.stringify(fresh.trajectory)!==JSON.stringify(trajectory)) {
          close();return;
        }
        const pair=await fetchOrthoLongitudinalCompare(
          patientId,caseId,fromOrdinal!,toOrdinal!,
        );
        if(serial!==epoch.current)return;
        if(!projectR6Presenter(fresh.trajectory,pair,userId,fromOrdinal,toOrdinal)) {
          close();return;
        }
        if(!presenter.current?.update(snapshot))close();
      } catch {
        if(serial===epoch.current)close();
      }
    };
    // Check immediately, then keep short-lived patient content current.
    void verify();
    const poll=window.setInterval(()=>{void verify();},9_000);
    const unsubscribe=useAuthStore.subscribe((state)=>{
      if(!state.isAuthenticated||normalizeR6PresenterUserId(state.user?.id)!==userId ||
         !hasAccess(state.user,'clinical')||!hasAccess(state.user,'patients'))close();
    });
    return()=>{epoch.current++;window.clearInterval(poll);unsubscribe();};
  },[opened,snapshot,allowed,trajectory,patientId,caseId,userId,fromOrdinal,toOrdinal,close]);

  const open=()=>{
    if(!snapshot||!allowed)return;
    setBlocked(false);
    close();
    const newPresenter=R6PresenterWindow.open(snapshot);
    if (!newPresenter) {setBlocked(true);return;}
    presenter.current=newPresenter;
    setOpened(true);
  };

  return (
    <div className="mt-3 rounded-xl border border-border-main bg-card/60 p-3"
      data-testid="r6d-patient-presenter-control">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-black text-text-main">Présentation patient · second écran</p>
          <p className="mt-1 text-[11px] text-text-muted">
            Fenêtre détachable, lecture seule, sans données de connexion ni interprétation automatique.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {opened && <button type="button" onClick={close}
            className="rounded-lg border border-border-main px-3 py-2 text-xs font-bold text-text-main">
            Fermer la présentation
          </button>}
          <button type="button" disabled={!snapshot} onClick={open}
            className="rounded-lg border border-border-main bg-background px-3 py-2 text-xs font-bold text-text-main disabled:opacity-40">
            {opened?'Rouvrir la présentation':'Ouvrir sur un autre écran'}
          </button>
        </div>
      </div>
      {!snapshot && <p role="status" className="mt-2 text-xs text-text-muted">
        Présentation indisponible : accès, sources ou comparaison canonique non vérifiés.
      </p>}
      {blocked && <p role="alert" className="mt-2 text-xs text-text-muted">
        Fenêtre bloquée par le navigateur : autorisez les fenêtres contextuelles pour ce site.
      </p>}
    </div>
  );
};
