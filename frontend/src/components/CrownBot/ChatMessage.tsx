import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, Check, X, Calendar, FileText, Pill } from 'lucide-react';

interface ChatMessageProps {
  message: {
    role: 'user' | 'bot';
    content: string;
    action_type?: string;
    pending_action?: any;
    data?: any;
  };
  onActionConfirm?: (actionType: string, params: any) => void;
  onActionCancel?: () => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  onActionConfirm,
  onActionCancel 
}) => {
  const isBot = message.role === 'bot';

  // Icône d'action en fonction du type
  const getActionIcon = (type: string) => {
    if (type === 'CREATE_APPOINTMENT') return <Calendar className="w-5 h-5 text-indigo-400" />;
    if (type === 'OPEN_DEVIS_EDITOR') return <FileText className="w-5 h-5 text-amber-400" />;
    if (type === 'OPEN_PRESCRIPTION_EDITOR') return <Pill className="w-5 h-5 text-emerald-400" />;
    return <Bot className="w-5 h-5 text-gray-400" />;
  };

  return (
    <div className={`flex w-full ${isBot ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`flex max-w-[85%] ${isBot ? 'flex-row' : 'flex-row-reverse'}`}>
        
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isBot ? 'bg-indigo-900/50 text-indigo-400 mr-3 border border-indigo-500/30' : 
                  'bg-gray-800 text-gray-300 ml-3 border border-gray-700'
        }`}>
          {isBot ? <Bot size={16} /> : <User size={16} />}
        </div>

        {/* Bubble */}
        <div className={`flex flex-col ${isBot ? 'items-start' : 'items-end'}`}>
          <div className={`px-4 py-3 rounded-2xl shadow-sm text-[15px] leading-relaxed ${
            isBot ? 'bg-[#1C1C21] text-gray-200 border border-white/5 rounded-tl-none' : 
                    'bg-indigo-600 text-white rounded-tr-none'
          }`}>
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  p: ({node, ...props}) => <p className="m-0" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-semibold text-white" {...props} />,
                  ul: ({node, ...props}) => <ul className="pl-4 m-0 list-disc opacity-90" {...props} />,
                  li: ({node, ...props}) => <li className="mb-1 last:mb-0" {...props} />,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          </div>

          {/* Action Card (pending_action) */}
          {message.pending_action && message.action_type === 'write_pending' && (
            <div className="mt-2 w-full max-w-[280px] bg-[#16161A] border border-indigo-500/30 rounded-xl p-3 shadow-lg">
              <div className="flex items-center gap-2 mb-3">
                {getActionIcon(message.pending_action.type)}
                <span className="text-sm font-medium text-gray-200">Action Requise</span>
              </div>
              
              <div className="flex gap-2">
                <button 
                  onClick={() => onActionConfirm?.(message.pending_action.type, message.pending_action.params)}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 transition-colors"
                >
                  <Check size={16} /> Confirmer
                </button>
                <button 
                  onClick={() => onActionCancel?.()}
                  className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 transition-colors"
                >
                  <X size={16} /> Annuler
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
