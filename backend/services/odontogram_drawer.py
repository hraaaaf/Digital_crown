from reportlab.lib import colors
from reportlab.lib.units import mm

class OdontogramDrawer:
    """
    Moteur de rendu schématique de l'odontogramme pour ReportLab.
    Dessine un schéma FDI (ISO 3950) simplifié.
    """
    
    def __init__(self):
        self.tooth_size = 6 * mm
        self.spacing = 1.2 * mm
        
    def draw(self, canvas, x, y, highlighted_teeth=None, p_color=colors.navy):
        """
        Dessine l'odontogramme anatomique à la position (x, y).
        """
        canvas.saveState()
        
        highlighted_teeth = [int(t) for t in highlighted_teeth] if highlighted_teeth else []
        
        # Quadrants FDI
        q1 = list(range(18, 10, -1))
        q2 = list(range(21, 29))
        q4 = list(range(48, 40, -1))
        q3 = list(range(31, 39))
        
        # Labels de quadrants
        canvas.setFont("Helvetica-Bold", 6)
        canvas.setFillColor(colors.lightgrey)
        canvas.drawString(x - 8*mm, y + self.tooth_size + 10*mm, "Q1")
        canvas.drawString(x + 16*(self.tooth_size + self.spacing) + 2*mm, y + self.tooth_size + 10*mm, "Q2")
        canvas.drawString(x + 16*(self.tooth_size + self.spacing) + 2*mm, y - 4*mm, "Q3")
        canvas.drawString(x - 8*mm, y - 4*mm, "Q4")

        # Dessin du haut (Maxillaire)
        self._draw_row(canvas, x, y + self.tooth_size + self.spacing, q1 + q2, highlighted_teeth, p_color, is_top=True)
        
        # Dessin du bas (Mandibule)
        self._draw_row(canvas, x, y, q4 + q3, highlighted_teeth, p_color, is_top=False)
        
        # Séparateur axial stylisé
        canvas.setStrokeColor(colors.lightgrey)
        canvas.setLineWidth(0.1)
        mid_x = x + 8 * (self.tooth_size + self.spacing) - self.spacing/2
        canvas.line(mid_x, y - 5*mm, mid_x, y + 2*self.tooth_size + 8*mm)
        
        # Ligne horizontale médiane
        canvas.line(x - 5*mm, y + self.tooth_size + self.spacing/2, x + 16*(self.tooth_size + self.spacing) + 2*mm, y + self.tooth_size + self.spacing/2)

        canvas.restoreState()

    def _draw_row(self, canvas, x, y, teeth_list, highlighted_teeth, p_color, is_top=True):
        current_x = x
        for t in teeth_list:
            is_highlighted = t in highlighted_teeth
            
            # Déterminer la forme (incisive vs molaire)
            is_molar = (t % 10) >= 4
            
            canvas.setLineWidth(0.5 if is_highlighted else 0.2)
            canvas.setStrokeColor(p_color if is_highlighted else colors.lightgrey)
            
            if is_highlighted:
                canvas.setFillColor(p_color)
                opac_color = colors.Color(p_color.red, p_color.green, p_color.blue, alpha=0.1)
                canvas.setFillColor(opac_color)
            else:
                canvas.setFillColor(colors.white)

            # Dessin de la forme anatomique simplifiée
            if is_molar:
                # Rectangle arrondi pour molaires
                canvas.roundRect(current_x, y, self.tooth_size, self.tooth_size, 1.5*mm, fill=1, stroke=1)
            else:
                # Arc/Cercle pour incisives/canines
                if is_top:
                    canvas.arc(current_x, y, current_x + self.tooth_size, y + self.tooth_size*1.5, 0, 180)
                    canvas.line(current_x, y, current_x + self.tooth_size, y)
                else:
                    canvas.arc(current_x, y - self.tooth_size*0.5, current_x + self.tooth_size, y + self.tooth_size, 180, 180)
                    canvas.line(current_x, y + self.tooth_size, current_x + self.tooth_size, y + self.tooth_size)
                
                # Fallback rect simple si arc trop complexe pour le remplissage rapide
                canvas.rect(current_x, y, self.tooth_size, self.tooth_size, fill=1, stroke=1)

            # Numéro de la dent
            canvas.setFont("Helvetica-Bold", 5)
            canvas.setFillColor(p_color if is_highlighted else colors.grey)
            
            text_y = y + self.tooth_size + 1.5*mm if is_top else y - 2.5*mm
            canvas.drawCentredString(current_x + self.tooth_size/2, text_y, str(t))
            
            current_x += self.tooth_size + self.spacing
