import React from 'react';
import { CrownBotChat } from '../../../../components/CrownBot/CrownBotChat';

export function BotView() {
  return (
    <div className="h-full bg-slate-50 flex flex-col">
      <div className="flex-1 overflow-hidden relative">
        <CrownBotChat />
      </div>
    </div>
  );
}
