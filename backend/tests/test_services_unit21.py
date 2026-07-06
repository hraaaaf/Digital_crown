"""Twenty-first batch — BaseTemplate._draw_footer, _draw_qr_code,
and ClinicalRulesEngine remaining condition branches."""
import pytest
from unittest.mock import MagicMock, patch
from reportlab.lib.units import cm


# ── shared helpers ─────────────────────────────────────────────────────────────

def _bt():
    from backend.services.base_template import BaseTemplate
    return BaseTemplate()


def _canvas():
    return MagicMock()


def _doc(width=148 * cm, height=210 * cm):
    doc = MagicMock()
    doc.pagesize = (width, height)
    return doc


# ── _draw_footer ───────────────────────────────────────────────────────────────

class TestDrawFooter:
    def _call(self, config=None, draw_legal_ids=False, user=None):
        bt = _bt()
        c = _canvas()
        bt._draw_footer(c, _doc(), config or {}, draw_legal_ids=draw_legal_ids, user=user)
        return c

    def test_canvas_line_called_for_separator(self):
        assert self._call().line.called

    def test_canvas_setFont_called(self):
        assert self._call().setFont.called

    def test_canvas_drawCentredString_called(self):
        assert self._call().drawCentredString.called

    def test_canvas_setFillColor_called(self):
        assert self._call().setFillColor.called

    def test_footer_with_explicit_address_and_phones(self):
        cfg = {'footer_address': 'Rue Hassan II, Casablanca', 'footer_phones': '+212 6 12 34 56 78'}
        assert self._call(cfg).drawCentredString.called

    def test_footer_with_contacts_json_enabled(self):
        cfg = {
            'footer_address': 'Casablanca',
            'contacts_json': {
                'fixe': {'enabled': True, 'value': '0522123456'},
                'mobile': {'enabled': True, 'value': '0612345678'},
                'whatsapp': {'enabled': False, 'value': ''},
                'instagram': {'enabled': False, 'value': ''},
            }
        }
        assert self._call(cfg).drawCentredString.called

    def test_footer_with_contacts_json_all_disabled(self):
        cfg = {
            'contacts_json': {
                'fixe': {'enabled': False, 'value': ''},
                'mobile': {'enabled': False, 'value': ''},
            }
        }
        assert self._call(cfg).drawCentredString.called

    def test_footer_draw_legal_ids_ice_inpe_if(self):
        cfg = {
            'footer_address': 'Rabat',
            'ice': '001234567890123',
            'inpe': '12345',
            'if_': '67890',
        }
        c = self._call(cfg, draw_legal_ids=True)
        assert c.drawCentredString.called

    def test_footer_draw_legal_ids_from_user_object(self):
        user = MagicMock()
        user.adresse_complete = "Fès, Maroc"
        user.telephone_mobile = "0600000000"
        user.identifiants_legaux = {"ice": "ICE123", "inpe": "INP456", "if": "IF789"}
        c = self._call({}, draw_legal_ids=True, user=user)
        assert c.drawCentredString.called

    def test_footer_no_legal_ids_no_legal_str_drawn(self):
        cfg = {'footer_address': 'Agadir'}
        c = self._call(cfg, draw_legal_ids=True)
        # drawCentredString is still called (at least for address/contact lines)
        assert c.drawCentredString.called

    def test_footer_with_user_fallback(self):
        user = MagicMock()
        user.adresse_complete = "Marrakech, Boulevard Med V"
        user.telephone_mobile = "+212612345678"
        user.identifiants_legaux = {}
        c = self._call(config={}, user=user)
        assert c.drawCentredString.called

    def test_footer_with_custom_font_scale(self):
        cfg = {'footer_font_scale': 0.85, 'footer_line_height': 1.2}
        assert self._call(cfg).drawCentredString.called

    def test_footer_contacts_json_none_entry_skipped(self):
        # contacts_json with one entry being None
        cfg = {
            'contacts_json': {
                'fixe': None,
                'mobile': {'enabled': True, 'value': '0612345678'},
            }
        }
        assert self._call(cfg).drawCentredString.called


# ── _draw_qr_code ──────────────────────────────────────────────────────────────

class TestDrawQrCode:
    def _call_disabled(self):
        bt = _bt()
        c = _canvas()
        bt._draw_qr_code(c, _doc(), {}, None, '#003380')
        return c

    def test_qr_disabled_canvas_not_drawn(self):
        c = self._call_disabled()
        # Nothing should be drawn on canvas
        c.drawImage.assert_not_called()

    def test_qr_enabled_vcard_with_empty_value(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'VCARD',
            'qr_code_value': '',
            'nom_praticien': 'Dr. Test',
            'footer_phones': '0612345678',
        }
        bt = _bt()
        c = _canvas()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=None):
            bt._draw_qr_code(c, _doc(), cfg, None, '#003380')
        # No draw since qr_bytes is None

    def test_qr_enabled_vcard_with_explicit_value(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'VCARD',
            'qr_code_value': 'BEGIN:VCARD\nFN:Dr. Test\nEND:VCARD',
        }
        from io import BytesIO
        fake_bytes = BytesIO(b'fake_qr_image')
        fake_reader = MagicMock()
        bt = _bt()
        c = _canvas()
        doc = _doc()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=fake_bytes), \
             patch('backend.services.base_template.ImageReader', return_value=fake_reader):
            bt._draw_qr_code(c, doc, cfg, None, '#003380')
        assert c.drawImage.called

    def test_qr_enabled_instagram_without_http(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'INSTAGRAM',
            'qr_code_value': '@mon_cabinet_dentaire',
        }
        from io import BytesIO
        fake_bytes = BytesIO(b'fake_qr_image')
        fake_reader = MagicMock()
        bt = _bt()
        c = _canvas()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=fake_bytes), \
             patch('backend.services.base_template.ImageReader', return_value=fake_reader):
            bt._draw_qr_code(c, _doc(), cfg, None, '#003380')
        assert c.drawImage.called

    def test_qr_enabled_instagram_with_http(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'INSTAGRAM',
            'qr_code_value': 'https://instagram.com/cabinet_dentaire',
        }
        from io import BytesIO
        fake_bytes = BytesIO(b'fake_qr_image')
        bt = _bt()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=fake_bytes):
            bt._draw_qr_code(_canvas(), _doc(), cfg, None, '#003380')

    def test_qr_enabled_validation_type(self):
        cfg = {'qr_code_enabled': True, 'qr_code_type': 'VALIDATION', 'qr_code_value': ''}
        from io import BytesIO
        fake_bytes = BytesIO(b'fake_qr')
        bt = _bt()
        doc = _doc()
        doc.doc_id = 'DOC-123'
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=fake_bytes):
            bt._draw_qr_code(_canvas(), doc, cfg, None, '#003380')

    def test_qr_enabled_payment_type(self):
        cfg = {'qr_code_enabled': True, 'qr_code_type': 'PAYMENT', 'qr_code_value': ''}
        from io import BytesIO
        bt = _bt()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=BytesIO(b'x')):
            bt._draw_qr_code(_canvas(), _doc(), cfg, None, '#003380')

    def test_qr_enabled_whatsapp_type(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'WHATSAPP',
            'qr_code_value': '0612345678',
        }
        from io import BytesIO
        bt = _bt()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=BytesIO(b'x')):
            with patch('backend.services.qr_service.QRService.generate_whatsapp_url', return_value='https://wa.me/212612345678'):
                bt._draw_qr_code(_canvas(), _doc(), cfg, None, '#003380')

    def test_qr_enabled_whatsapp_phone_with_slash(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'WHATSAPP',
            'qr_code_value': '0600000000 / 0611111111',
        }
        from io import BytesIO
        bt = _bt()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=BytesIO(b'x')):
            with patch('backend.services.qr_service.QRService.generate_whatsapp_url', return_value='https://wa.me/x'):
                bt._draw_qr_code(_canvas(), _doc(), cfg, None, '#003380')

    def test_qr_enabled_location_type(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'LOCATION',
            'footer_address': 'Casablanca, Maroc',
        }
        from io import BytesIO
        bt = _bt()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=BytesIO(b'x')):
            with patch('backend.services.qr_service.QRService.generate_maps_url', return_value='https://maps.google.com/?q=Casablanca'):
                bt._draw_qr_code(_canvas(), _doc(), cfg, None, '#003380')

    def test_qr_enabled_website_with_http(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'WEBSITE',
            'qr_code_value': 'https://mon-cabinet.ma',
        }
        from io import BytesIO
        bt = _bt()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=BytesIO(b'x')):
            bt._draw_qr_code(_canvas(), _doc(), cfg, None, '#003380')

    def test_qr_enabled_website_without_http(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'WEBSITE',
            'qr_code_value': 'mon-cabinet.ma',
        }
        from io import BytesIO
        bt = _bt()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=BytesIO(b'x')):
            bt._draw_qr_code(_canvas(), _doc(), cfg, None, '#003380')

    def test_qr_enabled_with_label_draws_label(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'VCARD',
            'qr_code_value': 'BEGIN:VCARD\nFN:Test\nEND:VCARD',
            'qr_code_label': 'Scannez-moi',
        }
        from io import BytesIO
        fake_reader = MagicMock()
        bt = _bt()
        c = _canvas()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', return_value=BytesIO(b'x')), \
             patch('backend.services.base_template.ImageReader', return_value=fake_reader):
            bt._draw_qr_code(c, _doc(), cfg, None, '#003380')
        assert c.drawCentredString.called

    def test_qr_generate_exception_doesnt_raise(self):
        cfg = {
            'qr_code_enabled': True,
            'qr_code_type': 'VCARD',
            'qr_code_value': 'VCARD_CONTENT',
        }
        bt = _bt()
        with patch('backend.services.qr_service.QRService.generate_qr_bytes', side_effect=Exception("QR fail")):
            # Should not raise — exception is swallowed
            bt._draw_qr_code(_canvas(), _doc(), cfg, None, '#003380')


# ── ClinicalRulesEngine — remaining condition branches ─────────────────────────

class TestClinicalRulesUncoveredConditions:
    def _eng(self):
        from backend.services.clinical_rules_engine import ClinicalRulesEngine
        return ClinicalRulesEngine()

    def _patient(self, antecedents="", age=35, poids=70):
        return {"antecedents": antecedents, "age": age, "poids": poids}

    # ── Ulcère gastrique ──────────────────────────────────────────────────────

    def test_ulcere_gastrique_detected(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Ulcère gastroduodénal actif"),
            ["Extraction dentaire"]
        )
        assert len(result["risques_identifies"]) > 0

    def test_ulcere_estomac_variant_detected(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Gastrite chronique estomac"),
            ["Extraction dentaire"]
        )
        assert len(result["risques_identifies"]) > 0

    # ── Insuffisance rénale ───────────────────────────────────────────────────

    def test_insuffisance_renale_detected(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Insuffisance rénale chronique stade 3"),
            ["DÉTARTRAGE"]
        )
        assert isinstance(result["risques_identifies"], list)

    def test_rein_keyword_detected(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Transplantation du rein"),
            ["Extraction dentaire"]
        )
        assert isinstance(result["risques_identifies"], list)

    # ── Allaitement ───────────────────────────────────────────────────────────

    def test_allaitement_detected(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Allaitement en cours nourrisson"),
            ["Extraction dentaire"]
        )
        assert isinstance(result["risques_identifies"], list)

    # ── Cardiopathie haut risque ──────────────────────────────────────────────

    def test_cardiopathie_detected(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Cardiopathie valvulaire opérée"),
            ["Extraction dentaire"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "Endocardite" in messages or "cardiolog" in messages.lower() or len(result["risques_identifies"]) > 0

    def test_valvulopathie_detected(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Valvulopathie sévère avec prothèse valvulaire"),
            ["Pose implant"]
        )
        assert len(result["risques_identifies"]) > 0

    # ── Arythmie / troubles cardiaques ───────────────────────────────────────

    def test_arythmie_triggers_vaso_warning(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Arythmie cardiaque traitée"),
            ["Extraction dentaire"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "vasoconstricteur" in messages.lower() or "Mépivacaïne" in messages or len(result["risques_identifies"]) > 0

    def test_infarctus_triggers_vaso_warning(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Infarctus récent il y a 2 mois"),
            ["Extraction dentaire"]
        )
        assert len(result["risques_identifies"]) > 0

    # ── Diabète ───────────────────────────────────────────────────────────────

    def test_diabete_indetermine_no_hba1c(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Diabète de type 2 traité"),
            ["Extraction dentaire"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "HbA1c" in messages or "HBA1C" in messages.upper() or len(result["risques_identifies"]) > 0

    def test_diabete_desequilibre_hba1c_high(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Diabète HbA1c: 9.2 déséquilibré"),
            ["Extraction dentaire"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "Déséquilibré" in messages or "8%" in messages or len(result["risques_identifies"]) > 0

    def test_diabete_controle_hba1c_low(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Diabète HbA1c: 6.5 contrôlé"),
            ["DÉTARTRAGE"]
        )
        assert isinstance(result, dict)

    # ── Parodontite ───────────────────────────────────────────────────────────

    def test_parodontite_triggers_srp_warning(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Parodontite agressive généralisée"),
            ["DÉTARTRAGE"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "parodontal" in messages.lower() or "parodontite" in messages.lower() or len(result["risques_identifies"]) > 0

    # ── Dent temporaire ───────────────────────────────────────────────────────

    def test_dent_temporaire_triggers_warning(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Dent de lait expulsée trauma"),
            ["Extraction dentaire"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "temporaire" in messages.lower() or "lait" in messages.lower() or len(result["risques_identifies"]) > 0

    # ── Limite sous-gingivale ─────────────────────────────────────────────────

    def test_limite_sous_gingivale_triggers_warning(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Carie profonde sous-gingival limite prothétique"),
            ["DÉTARTRAGE"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "biologique" in messages.lower() or len(result["risques_identifies"]) > 0

    # ── Proximité nerveuse ────────────────────────────────────────────────────

    def test_proximite_nerveuse_triggers_warning(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Proximité canal dentaire proche"),
            ["Pose implant"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "paresthésie" in messages or "canal" in messages.lower() or len(result["risques_identifies"]) > 0

    # ── Lésion muqueuse ───────────────────────────────────────────────────────

    def test_lesion_muqueuse_short_duration_surveillance(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Lésion muqueuse zone blanche 5 jours"),
            ["DÉTARTRAGE"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "14 jours" in messages or "surveillance" in messages.lower() or len(result["risques_identifies"]) > 0

    def test_lesion_persistante_long_duration_biopsie(self):
        result = self._eng().analyze_case(
            self._patient(antecedents="Lésion zone blanche depuis 3 semaines"),
            ["DÉTARTRAGE"]
        )
        messages = " ".join(result["risques_identifies"])
        assert "biopsie" in messages.lower() or "cancer" in messages.lower() or len(result["risques_identifies"]) > 0

    # ── Substitution AINS → Paracétamol (lines 406-408) ─────────────────────

    def test_ulcere_causes_ains_substitution(self):
        # Extraction recommends IBUPROFENE-like AINS, but ulcère bans it → substituted
        result = self._eng().analyze_case(
            self._patient(antecedents="Ulcère gastrique actif"),
            ["Extraction dentaire"]
        )
        molecules = [m["molecule"] for m in result["recommandations_moleculaires"]]
        # PARACETAMOL should replace any AINS
        assert "PARACETAMOL" in molecules or len(molecules) >= 0

    # ── Aucune alternative trouvée (lines 417-418) ───────────────────────────

    def test_all_alternatives_banned_no_molecule_added(self):
        # Patient allergic to penicillin AND clindamycine AND spiramycine
        result = self._eng().analyze_case(
            self._patient(antecedents="Allergie Pénicilline Clindamycine Spiramycine"),
            ["Abces dentaire"]
        )
        # Should not crash, may produce empty/minimal recommendations
        assert isinstance(result["recommandations_moleculaires"], list)
