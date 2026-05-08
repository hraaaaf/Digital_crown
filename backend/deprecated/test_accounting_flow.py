from backend import database, models, schemas
from backend.services.document_factory import DocumentFactory
from backend.services.archive_service import get_archive_service
from datetime import date
import os
import json

db = database.SessionLocal()

try:
    # 0. Setup Context
    patient = db.query(models.Patient).first()
    user = db.query(models.User).filter(models.User.role == "ADMIN").first() or db.query(models.User).first()

    if not patient or not user:
        print("ERREUR : Patient ou Utilisateur manquant pour le test.")
        exit(1)

    print(f"🧪 Test du flux comptable pour : {patient.nom} {patient.prenom} (ID: {patient.id})")

    doc_factory = DocumentFactory()
    archive_service = get_archive_service(db)

    # 1. Données de test pour la note d'honoraires
    data = schemas.HonorairesData(
        items=[
            schemas.HonoraireItem(designation="Test Flux Compta 1", montant=450.0),
            schemas.HonoraireItem(designation="Test Flux Compta 2", montant=150.0)
        ],
        total_lettres="Six cents Dirhams",
        facture_number="TEST-FLOW-2026",
        doc_date=date.today().isoformat()
    )

    # 2. Génération du PDF (Moteur ReportLab)
    print("--- Génération du PDF ---")
    pdf_path = doc_factory.create_note_honoraires(patient, data, db, user.id)
    print(f"PDF généré : {pdf_path}")

    # 3. Archivage (Simule POST /documents/generate)
    print("--- Archivage du document ---")
    source_path = os.path.abspath(pdf_path)
    if not os.path.exists(source_path):
        # Fallback pour chemins relatifs
        source_path = os.path.join(os.getcwd(), pdf_path)

    with open(source_path, "rb") as f:
        pdf_content = f.read()

    final_filename = f"NOTE_TEST_FLOW_{date.today().strftime('%d%m%Y')}.pdf"

    # Vérification anti-doublon (on force via un nouveau titre pour le test)
    doc, is_new_version = archive_service.archive_document(
        patient_id=patient.id,
        file_content=pdf_content,
        filename=final_filename,
        doc_type=models.DocumentType.NOTE_HONORAIRES,
        uploaded_by_id=user.id,
        clinical_data=data.model_dump(),
        title=f"Test Flux Comptable - {date.today().isoformat()}"
    )

    print(f"Archivage réussi : ID {doc.id}")
    print(f"Nouvelle version ? {'Oui' if is_new_version else 'Non'}")

    # 4. Vérification de la présence en comptabilité
    print("--- Vérification en Comptabilité ---")
    # Simulation de la requête backend de l'onglet Honoraires
    found_in_accounting = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
        models.DocumentArchive.id == doc.id
    ).first()

    if found_in_accounting:
        print("✅ SUCCÈS : La note est correctement enregistrée et visible dans le module comptabilité.")
        # Extraction du montant pour vérification
        total = 0.0
        if found_in_accounting.clinical_data and 'items' in found_in_accounting.clinical_data:
            total = sum(item.get('montant', 0) for item in found_in_accounting.clinical_data['items'])
        print(f"Vérification montant : {total} MAD")
    else:
        print("❌ ÉCHEC : La note n'apparaît pas dans les registres comptables.")

except Exception as e:
    print(f"❌ ERREUR CRITIQUE : {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
