/**
 * RVG Upload Modal
 * Allows users to upload intra-oral X-ray images with metadata.
 */
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Box,
  Typography,
  LinearProgress,
} from '@mui/material';
import rvgService, { RVGUploadRequest, RVGDocument } from '../../../services/rvgService';

interface RvgUploadModalProps {
  open: boolean;
  patientId: number;
  onClose: () => void;
  onSuccess: (doc: RVGDocument) => void;
  onError?: (error: any) => void;
}

const RADIO_TYPES = [
  { value: 'rvg', label: 'RVG' },
  { value: 'periapical', label: 'Périapicale' },
  { value: 'bitewing', label: 'Bitewing' },
  { value: 'occlusal', label: 'Occlusale' },
  { value: 'other', label: 'Autre intra-orale' },
];

export const RvgUploadModal: React.FC<RvgUploadModalProps> = ({
  open,
  patientId,
  onClose,
  onSuccess,
  onError,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [radioType, setRadioType] = useState('rvg');
  const [toothNumber, setToothNumber] = useState('');
  const [sector, setSector] = useState('');
  const [acquisitionDate, setAcquisitionDate] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);

      // Generate preview for images
      if (selectedFile.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          setPreview(event.target?.result as string);
        };
        reader.readAsDataURL(selectedFile);
      }
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Veuillez sélectionner un fichier.');
      return;
    }

    setLoading(true);
    setProgress(0);

    try {
      const request: RVGUploadRequest = {
        file,
        radio_type: radioType as any,
        tooth_number: toothNumber || undefined,
        sector: sector || undefined,
        acquisition_date: acquisitionDate || undefined,
        note: note || undefined,
      };

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress((p) => Math.min(p + 10, 90));
      }, 100);

      const doc = await rvgService.uploadRVG(patientId, request);

      clearInterval(progressInterval);
      setProgress(100);

      // Reset form
      setFile(null);
      setRadioType('rvg');
      setToothNumber('');
      setSector('');
      setAcquisitionDate('');
      setNote('');
      setPreview(null);
      setError(null);

      onSuccess(doc);
      setTimeout(() => onClose(), 500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du téléchargement.');
      if (onError) onError(err);
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setFile(null);
      setError(null);
      setPreview(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Ajouter une radio RVG</DialogTitle>

      <DialogContent sx={{ pt: 2 }}>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {/* File Input */}
        <Box sx={{ mb: 2 }}>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            onChange={handleFileChange}
            disabled={loading}
            style={{ display: 'block', marginBottom: 8 }}
          />
          <Typography variant="caption" color="textSecondary">
            Formats acceptés : JPEG, PNG, WebP, PDF (max 10 MB)
          </Typography>
        </Box>

        {/* Preview */}
        {preview && (
          <Box sx={{ mb: 2, textAlign: 'center' }}>
            <img src={preview} alt="Aperçu" style={{ maxWidth: '100%', maxHeight: 200, borderRadius: 4 }} />
          </Box>
        )}

        {/* Radio Type */}
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Type de radio</InputLabel>
          <Select
            value={radioType}
            onChange={(e) => setRadioType(e.target.value)}
            disabled={loading}
            label="Type de radio"
          >
            {RADIO_TYPES.map((rt) => (
              <MenuItem key={rt.value} value={rt.value}>
                {rt.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Tooth Number */}
        <TextField
          label="Dent concernée (optionnel)"
          value={toothNumber}
          onChange={(e) => setToothNumber(e.target.value)}
          disabled={loading}
          fullWidth
          size="small"
          sx={{ mb: 2 }}
          placeholder="ex: 16, 27, 38"
        />

        {/* Sector */}
        <TextField
          label="Secteur (optionnel)"
          value={sector}
          onChange={(e) => setSector(e.target.value)}
          disabled={loading}
          fullWidth
          size="small"
          sx={{ mb: 2 }}
          placeholder="ex: UR, LL"
        />

        {/* Acquisition Date */}
        <TextField
          label="Date de prise (optionnel)"
          type="date"
          value={acquisitionDate}
          onChange={(e) => setAcquisitionDate(e.target.value)}
          disabled={loading}
          fullWidth
          size="small"
          sx={{ mb: 2 }}
          InputLabelProps={{ shrink: true }}
        />

        {/* Note */}
        <TextField
          label="Note (optionnel)"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          disabled={loading}
          fullWidth
          multiline
          rows={3}
          size="small"
          sx={{ mb: 2 }}
          placeholder="Observations cliniques..."
        />

        {/* Progress */}
        {loading && progress > 0 && <LinearProgress variant="determinate" value={progress} sx={{ mb: 2 }} />}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Annuler
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!file || loading}
          startIcon={loading && <CircularProgress size={20} />}
        >
          {loading ? 'Téléchargement...' : 'Enregistrer'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default RvgUploadModal;
