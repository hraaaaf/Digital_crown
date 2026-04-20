import React from 'react';
import { AgendaStudio } from '../features/agenda/AgendaStudio';

export const AgendaPage: React.FC = () => {
  return (
    <div className="w-full h-full p-4 md:p-8 overflow-y-auto custom-scrollbar">
      <AgendaStudio />
    </div>
  );
};
