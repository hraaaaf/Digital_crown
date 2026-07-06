/**
 * Frontdesk Appointment Request Modal
 * Form for creating pending appointment requests manually
 */
import React, { useState } from 'react';
import { X } from 'lucide-react';
import { api } from '../../services/api';

interface FrontdeskModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  selectedDate?: Date;
}

export const FrontdeskModal: React.FC<FrontdeskModalProps> = ({
  open,
  onClose,
  onSuccess,
  selectedDate,
}) => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [reason, setReason] = useState('');
  const [date, setDate] = useState(selectedDate?.toISOString().split('T')[0] || '');
  const [time, setTime] = useState('10:00');
  const [duration, setDuration] = useState(30);
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const [h, m] = time.split(':').map(Number);
      const dateTime = new Date(`${date}T${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:00`);

      await api.post('/frontdesk/appointment-request', {
        first_name: firstName,
        last_name: lastName,
        phone: phone || undefined,
        appointment_reason: reason || undefined,
        requested_start: dateTime.toISOString(),
        duration_minutes: duration,
        source: 'frontdesk',
        notes: note || undefined,
      });

      // Reset form
      setFirstName('');
      setLastName('');
      setPhone('');
      setReason('');
      setNote('');
      setTime('10:00');
      setDuration(30);

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la création.');
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-bold">Nouvelle demande de RDV</h2>
          <button onClick={onClose} disabled={loading} className="p-2 hover:bg-gray-100 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="p-3 bg-red-100 text-red-700 rounded-lg text-sm">{error}</div>}

          <div className="grid grid-cols-2 gap-3">
            <input
              type="text"
              placeholder="Prénom"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
              disabled={loading}
              className="px-3 py-2 border rounded-lg text-sm"
            />
            <input
              type="text"
              placeholder="Nom"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
              disabled={loading}
              className="px-3 py-2 border rounded-lg text-sm"
            />
          </div>

          <input
            type="tel"
            placeholder="Téléphone (optionnel)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            disabled={loading}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          />

          <input
            type="text"
            placeholder="Motif de la visite"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={loading}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          />

          <div className="grid grid-cols-2 gap-3">
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              disabled={loading}
              className="px-3 py-2 border rounded-lg text-sm"
            />
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              required
              disabled={loading}
              className="px-3 py-2 border rounded-lg text-sm"
            />
          </div>

          <select
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            disabled={loading}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          >
            <option value={15}>15 minutes</option>
            <option value={30}>30 minutes</option>
            <option value={45}>45 minutes</option>
            <option value={60}>1 heure</option>
            <option value={90}>1h30</option>
            <option value={120}>2 heures</option>
          </select>

          <textarea
            placeholder="Notes (optionnel)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            disabled={loading}
            rows={3}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          />

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border rounded-lg font-medium hover:bg-gray-50"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Création...' : 'Créer demande'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FrontdeskModal;
