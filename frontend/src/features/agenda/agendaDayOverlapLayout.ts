/**
 * LOT07 / 07-A P2 — PRESENTATION ONLY.
 * Allocate horizontal lanes to appointments whose exact-time intervals overlap.
 * No mutation of patient, practitioner, conflict, or persisted appointment data.
 */
export interface AgendaDayInterval {
  id: number;
  datetime_start: string;
  duration_minutes: number;
}
export interface AgendaDayLane {
  lane: number;
  lanes: number;
  leftPercent: number;
  widthPercent: number;
}
export function layoutAgendaDayOverlaps<T extends AgendaDayInterval>(appointments: readonly T[]): Map<number, AgendaDayLane> {
  const positioned=appointments.map(appointment=>{
    const start=new Date(appointment.datetime_start).getTime();
    if(!Number.isFinite(start))return null;
    return {id:appointment.id,start,end:start+Math.max(15,appointment.duration_minutes||0)*60000};
  }).filter((item):item is {id:number;start:number;end:number}=>item!==null)
    .sort((a,b)=>a.start-b.start||a.end-b.end||a.id-b.id);
  const positions=new Map<number,AgendaDayLane>();
  let cluster:typeof positioned=[];
  let clusterEnd=Number.NEGATIVE_INFINITY;
  const flush=()=>{
    if(!cluster.length)return;
    const laneEnds:number[]=[];
    const allocated=cluster.map(event=>{
      let lane=laneEnds.findIndex(end=>end<=event.start);
      if(lane<0){lane=laneEnds.length;laneEnds.push(event.end);}
      else laneEnds[lane]=event.end;
      return {event,lane};
    });
    const lanes=laneEnds.length;
    for(const {event,lane} of allocated)
      positions.set(event.id,{lane,lanes,leftPercent:100*lane/lanes,widthPercent:100/lanes});
    cluster=[];
  };
  for(const item of positioned){
    if(cluster.length&&item.start>=clusterEnd){flush();clusterEnd=Number.NEGATIVE_INFINITY;}
    cluster.push(item);
    clusterEnd=Math.max(clusterEnd,item.end);
  }
  flush();
  return positions;
}
