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
    if (type === 'CREATE_APPOINTMENT') return <Calendar className="w-5 h-5 text-info" />;
    if (type === 'OPEN_DEVIS_EDITOR') return <FileText className="w-5 h-5 text-warning" />;
    if (type === 'OPEN_PRESCRIPTION_EDITOR') return <Pill className="w-5 h-5 text-success" />;
    return <Bot className="w-5 h-5 text-text-muted" />;
  };

  return (
    <div className={`flex w-full ${isBot ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`flex max-w-[85%] ${isBot ? 'flex-row' : 'flex-row-reverse'}`}>
        
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isBot ? 'bg-info-surface text-info mr-3 border border-border-main' : 
                  'bg-card text-text-muted ml-3 border border-border-main'
        }`}>
          {isBot ? <Bot size={16} /> : <User size={16} />}
        </div>

        {/* Bubble */}
        <div className={`flex flex-col ${isBot ? 'items-start' : 'items-end'}`}>
          <div className={`px-4 py-3 rounded-2xl shadow-sm text-[15px] leading-relaxed ${
            isBot ? 'bg-card text-text-main border border-border-main rounded-tl-none' : 
                    'bg-primary text-on-primary rounded-tr-none'
          }`}>
            <div className="max-w-none">
              <ReactMarkdown
                components={{
                  p: ({node, ...props}) => <p className="m-0" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-semibold" {...props} />,
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
            <div className="mt-2 w-full max-w-[280px] bg-card border border-border-main rounded-xl p-3 shadow-lg">
              <div className="flex items-center gap-2 mb-3">
                {getActionIcon(message.pending_action.type)}
                <span className="text-sm font-medium text-text-main">Action Requise</span>
              </div>
              
              <div className="flex gap-2">
                <button 
                  onClick={() => onActionConfirm?.(message.pending_action.type, message.pending_action.params)}
                  className="flex-1 bg-primary hover:bg-secondary text-on-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 transition-colors"
                >
                  <Check size={16} /> Confirmer
                </button>
                <button 
                  onClick={() => onActionCancel?.()}
                  className="flex-1 bg-card hover:bg-input-field text-text-muted py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 transition-colors"
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
