import React from 'react';

export const AnimatedBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden bg-transparent">
      
      {/* COUCHE 1 : MESH GRADIENT */}
      <div className="absolute inset-0 opacity-30">
        {/* Orbe Primaire */}
        <div 
          className="absolute -top-[20%] -left-[10%] w-[60%] h-[70%] rounded-full opacity-50 blur-[120px]"
          style={{ backgroundColor: 'var(--primary)', animation: 'drift-slow 25s ease-in-out infinite alternate' }}
        />
        {/* Orbe Secondaire */}
        <div 
          className="absolute top-[10%] -right-[20%] w-[50%] h-[80%] rounded-full opacity-40 blur-[140px]"
          style={{ backgroundColor: 'var(--secondary)', animation: 'drift-reverse 30s ease-in-out infinite alternate' }}
        />
        {/* Orbe Accent */}
        <div 
          className="absolute -bottom-[30%] left-[20%] w-[70%] h-[60%] rounded-full opacity-40 blur-[100px]"
          style={{ backgroundColor: 'var(--accent)', animation: 'drift-slow 35s ease-in-out infinite alternate-reverse' }}
        />
      </div>

      {/* COUCHE 2 : WIREFRAME TOPOLOGIQUE & INGÉNIERIE MÉDICALE */}
      <div 
        className="absolute inset-0 flex items-center justify-center opacity-[0.08]" 
        style={{ animation: 'pulse-soft 15s ease-in-out infinite' }}
      >
        <svg 
          width="150%" 
          height="150%" 
          viewBox="0 0 1000 800" 
          preserveAspectRatio="xMidYMid slice" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <g fill="none" stroke="var(--primary)" strokeWidth="0.5">
            {/* Lignes abstraites topographiques (rappelant l'onde d'un scanner 3D ou les couches de l'émail) */}
            <path d="M-100,300 C200,100 400,600 700,400 C900,250 1100,400 1100,400" />
            <path d="M-100,320 C200,120 400,620 700,420 C900,270 1100,420 1100,420" />
            <path d="M-100,340 C200,140 400,640 700,440 C900,290 1100,440 1100,440" />
            <path d="M-100,360 C200,160 400,660 700,460 C900,310 1100,460 1100,460" />
            <path d="M-100,380 C200,180 400,680 700,480 C900,330 1100,480 1100,480" />
            
            {/* Cercles d'ingénierie concentriques (représentation géométrique des proportions parfaites) */}
            <circle cx="250" cy="500" r="200" strokeDasharray="4 8" />
            <circle cx="250" cy="500" r="140" strokeWidth="0.2" />
            <circle cx="250" cy="500" r="80" strokeDasharray="1 15" strokeWidth="0.8" />
            
            <circle cx="850" cy="250" r="350" strokeDasharray="2 12" />
            <circle cx="850" cy="250" r="280" strokeWidth="0.3" />
            <circle cx="850" cy="250" r="220" strokeDasharray="15 5" strokeWidth="0.1" />
            <circle cx="850" cy="250" r="100" strokeWidth="0.1" />
            
            {/* Connecteurs géométriques (lignes de repère d'implants) */}
            <line x1="250" y1="500" x2="850" y2="250" strokeWidth="0.2" strokeDasharray="5 5" />
            <circle cx="550" cy="375" r="5" strokeWidth="1" />
          </g>
        </svg>
      </div>
    </div>
  );
};
