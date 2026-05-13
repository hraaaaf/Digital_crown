import React from 'react';
import { motion } from 'framer-motion';
import { EliteAssistant } from './EliteAssistant';
import { TourLauncher } from '../../../components/GuidedTour/TourLauncher';
import { useEliteStore } from '../../../stores/useEliteStore';

interface EliteDockProps {
  insights?: any[];
  intelligenceScore?: number;
}

export const EliteDock: React.FC<EliteDockProps> = ({ insights = [], intelligenceScore = 85 }) => {
  const { dockPosition, setDockPosition } = useEliteStore();

  return (
    <motion.div
      drag
      dragMomentum={false}
      onDragEnd={(_, info) => {
        setDockPosition({ 
          x: dockPosition.x + info.offset.x, 
          y: dockPosition.y + info.offset.y 
        });
      }}
      initial={{ x: dockPosition.x, y: dockPosition.y, opacity: 0 }}
      animate={{ x: dockPosition.x, y: dockPosition.y, opacity: 1 }}
      className="fixed top-5 right-[360px] z-[999] flex items-center gap-1.5 pointer-events-auto cursor-grab active:cursor-grabbing group"
    >
      {/* GUIDE ORB (Embedded) */}
      <TourLauncher isEmbedded />

      {/* BRAIN ORB (Embedded) */}
      <EliteAssistant 
        insights={insights} 
        intelligenceScore={intelligenceScore} 
        isEmbedded 
      />
    </motion.div>
  );
};
