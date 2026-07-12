"""
Tests unitaires purs pour classify_acte_type (UNIFY-ACT-PERSISTENCE-1).
Aucune connexion DB. Exécuter avec : pytest backend/tests/test_acte_classification.py -v
"""
from backend import models
from backend.services.acte_classification import classify_acte_type


class TestClassifyActeType:
    def test_empty_or_none_defaults_to_soin(self):
        assert classify_acte_type("") == models.ActeType.SOIN
        assert classify_acte_type(None) == models.ActeType.SOIN

    def test_prothese_keywords(self):
        for libelle in ["Couronne céramique", "Bridge 3 éléments", "Pose implant", "Facette céramique", "Inlay/Onlay"]:
            assert classify_acte_type(libelle) == models.ActeType.PROTHESE, libelle

    def test_ortho_contention_keyword(self):
        assert classify_acte_type("Pose contention fixe") == models.ActeType.ORTHO_CONTENTION

    def test_ortho_semestre_keywords(self):
        for libelle in ["Semestre ODF multibagues", "Appareil ortho fixe", "Pose bagues"]:
            assert classify_acte_type(libelle) == models.ActeType.ORTHO_SEMESTRE, libelle

    def test_unrecognized_defaults_to_soin(self):
        assert classify_acte_type("Détartrage & Polissage") == models.ActeType.SOIN
        assert classify_acte_type("Consultation standard") == models.ActeType.SOIN

    def test_contention_takes_priority_over_ortho(self):
        # "Contention orthodontique" contient les deux familles de mots-clés — la
        # contention doit primer (ordre de priorité du helper).
        assert classify_acte_type("Contention orthodontique") == models.ActeType.ORTHO_CONTENTION
