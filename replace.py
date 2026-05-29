import sys

file_path = "backend/services/base_template.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.startswith("    def _draw_auto_header"):
        start_idx = i
    if line.startswith("    def _draw_footer"):
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_code = """    def _draw_auto_header(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height):
        \"\"\"
        En-tête Elite : Répartit et applique le design selon selected_template.
        \"\"\"
        selected_template = self._get_val(config, 'selected_template', 'swiss')
        
        fr_lines = self._get_val(config, 'header_lines_fr')
        if not fr_lines: fr_lines = ["Dr. Nom Prénom", "Chirurgien Dentiste"]
        
        ar_lines = self._get_val(config, 'header_lines_ar')
        if not ar_lines: ar_lines = ["د. الإسم الكامل", "طبيب جراح للأسنان"]

        # Échelle globale de l'en-tête
        h_scale = self._get_val(config, 'header_scale', 1.0)

        if selected_template == 'royal':
            self._draw_header_royal(canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale)
        else: # swiss (default)
            self._draw_header_swiss(canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale)

    def _draw_header_swiss(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
        # Swiss Clinic (Asymétrique): Ligne Claire, structure asymétrique, pur
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        
        margin = 1.5*cm
        y_top = p_height - 1.8*cm
        
        hf_scale = self._get_val(config, 'header_font_scale', 1.0) * h_scale
        hl_scale = self._get_val(config, 'header_logo_scale', 1.0) * h_scale
        lh_scale = self._get_val(config, 'header_line_height', 1.0)

        line_height = 0.45*cm * lh_scale
        logo_size = 2.2*cm * hl_scale
        
        # Logo on the top left
        if logo_path:
            canvas.drawImage(logo_path, margin, y_top - logo_size + 0.3*cm, width=logo_size, height=logo_size, mask='auto')
            text_x = margin + logo_size + 0.8*cm
        else:
            text_x = margin
            
        column_w = (p_width - text_x - margin) / 2.0

        # French Text
        fs_list = []
        for i, line in enumerate(fr_lines):
            base_fs = 26 * hf_scale
            font = self.header_bold if i == 0 else self.header_font
            fs_list.append(self.get_adaptive_font_size(line, font, base_fs, column_w))
        common_fs = min(fs_list) if fs_list else 26 * hf_scale

        curr_y = y_top
        for i, line in enumerate(fr_lines):
            font = self.header_bold if i == 0 else self.header_font
            canvas.setFillColor(p_color if i == 0 else colors.HexColor('#334155'))
            canvas.setFont(font, common_fs)
            canvas.drawString(text_x, curr_y, line)
            curr_y -= line_height

        # Arabic Text (Right aligned)
        font_ar = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        fs_list_ar = []
        for i, line in enumerate(ar_lines):
            base_fs = (28 if font_ar != 'Helvetica' else 20) * hf_scale
            fs_list_ar.append(self.get_adaptive_font_size(line, font_ar, base_fs, column_w))
        common_fs_ar = min(fs_list_ar) if fs_list_ar else (28 if font_ar != 'Helvetica' else 20) * hf_scale

        curr_y = y_top
        for i, line in enumerate(ar_lines):
            canvas.setFillColor(p_color if i == 0 else colors.HexColor('#334155'))
            canvas.setFont(font_ar, common_fs_ar)
            prepared_text = self._prepare_arabic(line)
            canvas.drawRightString(p_width - margin, curr_y, prepared_text)
            curr_y -= line_height

        # Minimalist horizontal delimiter
        canvas.saveState()
        canvas.setStrokeColor(a_color)
        canvas.setLineWidth(1)
        # Small accent line at the bottom left
        canvas.line(margin, p_height - 3.8*cm, margin + 4.0*cm, p_height - 3.8*cm)
        canvas.restoreState()

    def _draw_header_royal(self, canvas, config, logo_path, p_color, s_color, a_color, p_width, p_height, fr_lines, ar_lines, h_scale):
        # Royal Elite (Classique): Centered, elegant, regal
        from reportlab.lib.units import cm
        from reportlab.lib import colors

        hf_scale = self._get_val(config, 'header_font_scale', 1.0) * h_scale
        hl_scale = self._get_val(config, 'header_logo_scale', 1.0) * h_scale
        lh_scale = self._get_val(config, 'header_line_height', 1.0)

        # Subtle thin border at the very top
        canvas.saveState()
        canvas.setStrokeColor(p_color)
        canvas.setLineWidth(1.5)
        canvas.line(1.5*cm, p_height - 0.8*cm, p_width - 1.5*cm, p_height - 0.8*cm)
        canvas.setLineWidth(0.5)
        canvas.line(1.5*cm, p_height - 0.95*cm, p_width - 1.5*cm, p_height - 0.95*cm)
        canvas.restoreState()

        # Logo at top center
        logo_size = 2.2*cm * hl_scale
        y_start = p_height - 1.3*cm
        if logo_path:
            logo_y = y_start - logo_size
            canvas.drawImage(logo_path, (p_width - logo_size)/2, logo_y, width=logo_size, height=logo_size, mask='auto')
            y_start = logo_y - 0.5*cm
        
        line_height = 0.45*cm * lh_scale
        column_w = p_width - 4.0*cm

        # French
        fs_list = []
        for i, line in enumerate(fr_lines):
            base_fs = 26 * hf_scale
            font = self.header_bold if i == 0 else self.header_font
            fs_list.append(self.get_adaptive_font_size(line, font, base_fs, column_w))
        common_fs = min(fs_list) if fs_list else 26 * hf_scale

        curr_y = y_start
        for i, line in enumerate(fr_lines):
            font = self.header_bold if i == 0 else self.header_font
            canvas.setFillColor(p_color)
            canvas.setFont(font, common_fs)
            canvas.drawCentredString(p_width/2, curr_y, line)
            curr_y -= line_height

        # Royal Divider
        curr_y -= 0.1*cm
        canvas.saveState()
        canvas.setStrokeColor(p_color)
        canvas.setLineWidth(0.5)
        # Line - dot - diamond - dot - Line
        canvas.line(p_width/2 - 3.0*cm, curr_y, p_width/2 - 0.8*cm, curr_y)
        canvas.line(p_width/2 + 0.8*cm, curr_y, p_width/2 + 3.0*cm, curr_y)
        
        canvas.setFillColor(a_color)
        canvas.circle(p_width/2 - 0.5*cm, curr_y, 0.05*cm, fill=True, stroke=False)
        canvas.circle(p_width/2 + 0.5*cm, curr_y, 0.05*cm, fill=True, stroke=False)
        
        canvas.setFont(self.header_bold, 8)
        canvas.drawCentredString(p_width/2, curr_y - 0.1*cm, "✦")
        canvas.restoreState()
        
        curr_y -= 0.5*cm

        # Arabic
        font_ar = self.arabic_font if hasattr(self, 'arabic_font') else "Helvetica"
        fs_list_ar = []
        for i, line in enumerate(ar_lines):
            base_fs = (28 if font_ar != 'Helvetica' else 20) * hf_scale
            fs_list_ar.append(self.get_adaptive_font_size(line, font_ar, base_fs, column_w))
        common_fs_ar = min(fs_list_ar) if fs_list_ar else (28 if font_ar != 'Helvetica' else 20) * hf_scale

        for i, line in enumerate(ar_lines):
            canvas.setFillColor(p_color)
            canvas.setFont(font_ar, common_fs_ar)
            prepared_text = self._prepare_arabic(line)
            canvas.drawCentredString(p_width/2, curr_y, prepared_text)
            curr_y -= line_height

"""
    lines[start_idx:end_idx] = [new_code]
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Replaced successfully")
else:
    print(f"Error finding indices: start_idx={start_idx}, end_idx={end_idx}")
