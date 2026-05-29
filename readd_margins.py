import sys

file_path = "backend/services/base_template.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_method = """
    def get_document_margins(self, config, p_width):
        from reportlab.lib.units import cm
        selected_template = self._get_val(config, 'selected_template', 'swiss')
        
        m_top = 4.0 * cm
        m_bottom = 2.5 * cm
        m_left = 1.5 * cm
        m_right = 1.5 * cm
        
        if selected_template == 'royal':
            m_top = 4.5 * cm
            m_left = 2.0 * cm
            m_right = 2.0 * cm
        elif selected_template == 'swiss':
            m_top = 4.2 * cm
            m_left = 1.5 * cm
            m_right = 1.5 * cm
            
        return m_top, m_bottom, m_left, m_right
"""

if "def get_document_margins" not in content:
    # insert before draw_static_elements
    idx = content.find("def draw_static_elements")
    if idx != -1:
        content = content[:idx] + new_method + "\n    " + content[idx:]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Added get_document_margins")
    else:
        print("Could not find draw_static_elements")
else:
    print("already exists")
