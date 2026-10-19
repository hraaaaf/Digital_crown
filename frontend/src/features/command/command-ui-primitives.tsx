/** LOT07/07-C — shared small presentational primitives, no Cabinet state. */
import type {ReactNode} from 'react';

export type Tone='success'|'warning'|'danger'|'info';
export function Pill({children,tone='info'}:{children:ReactNode;tone?:Tone}){
 return <span className={'cmd-pill cmd-pill-'+tone}>{children}</span>;
}
export function Card({title,action,children,className='',hidden=false,id}:{title:string;action?:ReactNode;children:ReactNode;className?:string;hidden?:boolean;id?:string}){
 return <section id={id} tabIndex={id?-1:undefined} hidden={hidden} className={'cmd-card '+className}><header className="cmd-cardhead"><h3>{title}</h3>{action}</header>{children}</section>;
}
