/**
 * Pending Request Card Component
 * Displays a pending frontdesk appointment request with action buttons
 */
import React, { useState } from 'react';
import { api } from '../../services/api';
import { AlertCircle, CheckCircle, XCircle, Clock } from 'lucide-react';

export interface PendingRequest {
  id: number;
  patient_name: string | null;
  phone?: string | null;
  datetime_start: string;
  duration_minutes: number;
  motif?: string | null;
  status: string;
  source?: string | null;
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
    'EN_ATTENTE_DEMANDE': <AlertCircle className="text-warning" size={20} />,
    'EN_ATTENTE_CONFIRM': <Clock className="text-warning" size={20} />,
  }[request.status];

  const statusBg = {
    'EN_ATTENTE_DEMANDE': 'bg-warning-surface border-warning-border',
    'EN_ATTENTE_CONFIRM': 'bg-warning-surface border-warning-border',
  }[request.status] || 'bg-card border-border-main';

  return (
    <div className={`border-2 ${statusBg} rounded-xl p-4 shadow-md`}>
      <div className="flex items-start gap-3 mb-3">
        {statusIcon}
        <div className="flex-1">
          <h3 className="font-bold text-lg">{request.patient_name || "Demande de rendez-vous — identité masquée"}</h3>
          {request.phone && <p className="text-sm text-text-muted">📱 {request.phone}</p>}
          {request.motif && <p className="text-sm text-text-muted">💊 {request.motif}</p>}
        </div>
      </div>

      <div className="space-y-2 mb-4 text-sm">
        <p className="text-text-main">
          <strong>Créneau :</strong> {dateStr} à {timeStr} ({request.duration_minutes} min)
        </p>
        {request.source && <p className="text-text-muted"><strong>Source :</strong> {request.source}</p>}
        {request.expires_at && (
          <p className="text-danger text-xs">
            ⏰ Expire {new Date(request.expires_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>

      {showConfirmTemplate && (
        <div className="bg-info-surface border border-info-border rounded-lg p-3 mb-4 text-xs">
          <p className="text-info">
            Message template copié. Envoyez à {request.patient_name} :
          </p>
        </div>
      )}

      {!request.patient_name && (
        <p role="status" className="mb-3 text-xs text-text-muted">Informations réservées aux utilisateurs autorisés à consulter les patients.</p>
      )}

      <div className="flex gap-2">
        {request.status === 'EN_ATTENTE_DEMANDE' ? (
          <>
            <button
              onClick={handleRequestConfirm}
              disabled={loading || !request.patient_name}
              title={!request.patient_name ? "Droit Patients requis pour une confirmation nominative" : undefined}
              className="flex-1 px-3 py-2 border border-warning-border bg-warning-surface text-warning text-sm font-medium rounded-lg hover:bg-warning-border disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              Demander confirmation
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="flex-1 px-3 py-2 bg-primary text-on-primary text-sm font-medium rounded-lg hover:bg-secondary disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              Confirmer
            </button>
          </>
        ) : (
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="flex-1 px-3 py-2 bg-primary text-on-primary text-sm font-medium rounded-lg hover:bg-secondary disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Confirmer
          </button>
        )}
        <button
          onClick={handleReject}
          disabled={loading}
          className="flex-1 px-3 py-2 border border-danger-border bg-danger-surface text-danger text-sm font-medium rounded-lg hover:bg-danger-border disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        >
          Refuser
        </button>
      </div>
    </div>
  );
};

export default PendingRequestCard;
