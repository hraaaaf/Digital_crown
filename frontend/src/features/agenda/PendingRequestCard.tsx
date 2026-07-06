/**
 * Pending Request Card Component
 * Displays a pending frontdesk appointment request with action buttons
 */
import React, { useState } from 'react';
import { api } from '../../services/api';
import { AlertCircle, CheckCircle, XCircle, Clock } from 'lucide-react';

export interface PendingRequest {
  id: number;
  patient_name: string;
  phone?: string;
  datetime_start: string;
  duration_minutes: number;
  motif?: string;
  status: string;
  source?: string;
  expires_at?: string;
  created_at: string;
}

interface PendingRequestCardProps {
  request: PendingRequest;
  onAction: () => void;
}

export const PendingRequestCard: React.FC<PendingRequestCardProps> = ({ request, onAction }) => {
  const [loading, setLoading] = useState(false);
  const [showConfirmTemplate, setShowConfirmTemplate] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await api.post(`/appointments/${request.id}/confirm`);
      onAction();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erreur lors de la confirmation');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestConfirm = async () => {
    setLoading(true);
    try {
      const res = await api.post(`/appointments/${request.id}/request-confirmation`);
      setShowConfirmTemplate(true);
      onAction();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erreur lors de la demande de confirmation');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!window.confirm('Êtes-vous sûr de refuser cette demande ?')) return;
    setLoading(true);
    try {
      await api.post(`/appointments/${request.id}/reject`);
      onAction();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erreur lors du refus');
    } finally {
      setLoading(false);
    }
  };

  const dateTime = new Date(request.datetime_start);
  const dateStr = dateTime.toLocaleDateString('fr-FR', { weekday: 'short', month: 'short', day: 'numeric' });
  const timeStr = dateTime.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

  const statusIcon = {
    'EN_ATTENTE_DEMANDE': <AlertCircle className="text-orange-600" size={20} />,
    'EN_ATTENTE_CONFIRM': <Clock className="text-yellow-600" size={20} />,
  }[request.status];

  const statusBg = {
    'EN_ATTENTE_DEMANDE': 'bg-orange-50 border-orange-200',
    'EN_ATTENTE_CONFIRM': 'bg-yellow-50 border-yellow-200',
  }[request.status] || 'bg-gray-50 border-gray-200';

  return (
    <div className={`border-2 ${statusBg} rounded-xl p-4 shadow-md`}>
      <div className="flex items-start gap-3 mb-3">
        {statusIcon}
        <div className="flex-1">
          <h3 className="font-bold text-lg">{request.patient_name}</h3>
          {request.phone && <p className="text-sm text-gray-600">📱 {request.phone}</p>}
          {request.motif && <p className="text-sm text-gray-600">💊 {request.motif}</p>}
        </div>
      </div>

      <div className="space-y-2 mb-4 text-sm">
        <p className="text-gray-700">
          <strong>Créneau :</strong> {dateStr} à {timeStr} ({request.duration_minutes} min)
        </p>
        {request.source && <p className="text-gray-600"><strong>Source :</strong> {request.source}</p>}
        {request.expires_at && (
          <p className="text-red-600 text-xs">
            ⏰ Expire {new Date(request.expires_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>

      {showConfirmTemplate && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-xs">
          <p className="text-blue-900">
            Message template copié. Envoyez à {request.patient_name} :
          </p>
        </div>
      )}

      <div className="flex gap-2">
        {request.status === 'EN_ATTENTE_DEMANDE' ? (
          <>
            <button
              onClick={handleRequestConfirm}
              disabled={loading}
              className="flex-1 px-3 py-2 bg-yellow-500 text-white text-sm font-medium rounded-lg hover:bg-yellow-600 disabled:opacity-50"
            >
              Demander confirmation
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Confirmer
            </button>
          </>
        ) : (
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Confirmer
          </button>
        )}
        <button
          onClick={handleReject}
          disabled={loading}
          className="flex-1 px-3 py-2 bg-red-100 text-red-700 text-sm font-medium rounded-lg hover:bg-red-200 disabled:opacity-50"
        >
          Refuser
        </button>
      </div>
    </div>
  );
};

export default PendingRequestCard;
