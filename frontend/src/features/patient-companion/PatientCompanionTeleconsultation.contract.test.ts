import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const patient = readFileSync(resolve(process.cwd(), 'src/features/patient-companion/PatientCompanionTeleconsultation.tsx'), 'utf8');
const staff = readFileSync(resolve(process.cwd(), 'src/features/patients/components/PatientCompanionTeleconsultationPanel.tsx'), 'utf8');
const transport = readFileSync(resolve(process.cwd(), 'src/features/patient-companion/PatientCompanionTeleconsultTransport.ts'), 'utf8');

describe('PC-09 teleconsultation truth contract', () => {
  it('requests camera and microphone only from an explicit join/start handler', () => {
    expect(patient).toContain("getUserMedia({ video: true, audio: true })");
    expect(patient).toContain("onClick={() => void join(shown)}");
    expect(patient).toContain("Accepter et rejoindre");
    expect(patient).toContain("vous acceptez cette téléconsultation");
    expect(patient).toContain("Aucun enregistrement.");
    expect(staff).toContain("getUserMedia({ video: true, audio: true })");
    expect(staff).toContain("Démarrer une téléconsultation");
  });

  it('offers explicit accept and decline actions before media starts', () => {
    expect(patient).toContain("Accepter et rejoindre");
    expect(patient).toContain("Refuser");
    expect(patient).toContain("PatientCompanionTeleconsultTransport.reject");
    expect(transport).toContain("'teleconsult.reject'");
    expect(transport).toContain("'CREATED'");
  });

  it('reports connected only from the real WebRTC connection state', () => {
    expect(patient).toContain("peer.connectionState === 'connected'");
    expect(patient).toContain("PatientCompanionTeleconsultTransport.connected");
    expect(staff).toContain("peer.connectionState === 'connected'");
    expect(staff).toContain("/connected");
  });

  it('keeps media out of application signaling payloads', () => {
    expect(patient).toContain("signal_type");
    expect(patient).not.toContain("MediaRecorder");
    expect(staff).not.toContain("MediaRecorder");
    expect(patient).not.toContain("recording");
    expect(staff).not.toContain("recording");
  });

  it('persists real peer failure instead of leaving a false connecting state', () => {
    expect(patient).toContain("peer.connectionState === 'failed'");
    expect(patient).toContain("PatientCompanionTeleconsultTransport.failed");
    expect(staff).toContain("peer.connectionState === 'failed'");
    expect(staff).toContain("PEER_CONNECTION_FAILED");
    expect(transport).toContain("'teleconsult.failed'");
  });

  it('fails closed media when session control is lost', () => {
    expect(patient).toContain("cleanupPeer();");
    expect(patient).toContain("Synchronisation de la consultation impossible.");
    expect(staff).toContain("stopPeer();");
    expect(staff).toContain("Connexion au patient interrompue.");
  });

  it('ends tracks and peer connection explicitly', () => {
    expect(patient).toContain("track.stop()");
    expect(patient).toContain("peerRef.current?.close()");
    expect(staff).toContain("track.stop()");
    expect(staff).toContain("peerRef.current?.close()");
  });
});
