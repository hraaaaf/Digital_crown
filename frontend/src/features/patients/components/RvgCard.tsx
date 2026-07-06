/**
 * RVG Card Component
 * Displays a single RVG document with metadata and action buttons.
 */
import React from 'react';
import {
  Card,
  CardMedia,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Delete as DeleteIcon, Download as DownloadIcon, OpenInNew as OpenIcon } from '@mui/icons-material';
import { RVGDocument } from '../../../services/rvgService';
import AuthImg from '../../../components/Auth/AuthImg';
import { useAuthenticatedImage } from '../../../hooks/useAuthenticatedImage';
import rvgService from '../../../services/rvgService';

interface RvgCardProps {
  doc: RVGDocument;
  onDelete?: (docId: number) => void;
  canDelete?: boolean;
  canDownload?: boolean;
}

export const RvgCard: React.FC<RvgCardProps> = ({
  doc,
  onDelete,
  canDelete = false,
  canDownload = true,
}) => {
  const [deleteConfirmOpen, setDeleteConfirmOpen] = React.useState(false);
  const [opening, setOpening] = React.useState(false);

  const handleOpenFile = async () => {
    setOpening(true);
    try {
      // Open file in new tab with auth token
      const token = localStorage.getItem('token');
      const url = rvgService.getDownloadUrl(doc.id, token);
      window.open(url, '_blank');
    } catch (err) {
      console.error('Error opening file:', err);
    } finally {
      setOpening(false);
    }
  };

  const handleDownload = async () => {
    try {
      const token = localStorage.getItem('token');
      const url = rvgService.getDownloadUrl(doc.id, token);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.original_filename || `rvg_${doc.id}`;
      a.click();
    } catch (err) {
      console.error('Error downloading file:', err);
    }
  };

  const handleDeleteConfirm = async () => {
    if (onDelete) {
      try {
        await rvgService.deleteRVG(doc.id);
        onDelete(doc.id);
      } catch (err) {
        console.error('Error deleting RVG:', err);
      }
    }
    setDeleteConfirmOpen(false);
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('fr-FR');
    } catch {
      return dateStr;
    }
  };

  const radioTypeLabel = {
    rvg: 'RVG',
    periapical: 'Périapicale',
    bitewing: 'Bitewing',
    occlusal: 'Occlusale',
    other: 'Autre',
  }[doc.clinical_data?.radio_type] || doc.clinical_data?.radio_type || 'Radio';

  return (
    <>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Thumbnail */}
        <Box sx={{ height: 200, backgroundColor: '#f5f5f5', overflow: 'hidden' }}>
          {doc.original_filename?.toLowerCase().endsWith('.pdf') ? (
            <Box
              sx={{
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                color: '#999',
              }}
            >
              <Typography variant="h6">📄 PDF</Typography>
              <Typography variant="caption">{doc.original_filename}</Typography>
            </Box>
          ) : (
            <AuthImg
              src={doc.download_url}
              alt={`${radioTypeLabel} - ${doc.original_filename}`}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
          )}
        </Box>

        {/* Metadata */}
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ mb: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip label={radioTypeLabel} size="small" variant="outlined" />
            {doc.clinical_data?.tooth_number && (
              <Chip label={`Dent ${doc.clinical_data.tooth_number}`} size="small" />
            )}
            {doc.clinical_data?.sector && (
              <Chip label={`Secteur ${doc.clinical_data.sector}`} size="small" />
            )}
          </Box>

          {doc.clinical_data?.acquisition_date && (
            <Typography variant="caption" display="block" color="textSecondary" sx={{ mb: 1 }}>
              Prise le : {formatDate(doc.clinical_data.acquisition_date)}
            </Typography>
          )}

          {doc.clinical_data?.note && (
            <Typography variant="body2" sx={{ mb: 1 }}>
              {doc.clinical_data.note}
            </Typography>
          )}

          <Typography variant="caption" display="block" color="textSecondary">
            Ajoutée le {formatDate(doc.created_at)}
          </Typography>
        </CardContent>

        {/* Actions */}
        <CardActions sx={{ pt: 0 }}>
          <Button
            size="small"
            startIcon={<OpenIcon />}
            onClick={handleOpenFile}
            disabled={opening}
          >
            Ouvrir
          </Button>
          {canDownload && (
            <Button
              size="small"
              startIcon={<DownloadIcon />}
              onClick={handleDownload}
            >
              Télécharger
            </Button>
          )}
          {canDelete && (
            <Button
              size="small"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteConfirmOpen(true)}
            >
              Supprimer
            </Button>
          )}
        </CardActions>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirmer la suppression</DialogTitle>
        <DialogContent>
          Êtes-vous sûr de vouloir supprimer cette radio ?
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Annuler</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Supprimer
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default RvgCard;
