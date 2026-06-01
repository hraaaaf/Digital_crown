import re
from typing import Tuple, Dict

class DataSanitizer:
    def __init__(self):
        # Règles de détection (Regex) simples pour l'approche hybride
        self.rules = {
            "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "PHONE": r"(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}|(?:(?:\+|00)212|0)[5-7](?:[\s.-]*\d{2}){4}",
            "DATE": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            # Détection naïve de noms propres (Mots commençant par une majuscule au milieu de la phrase)
            "NAME": r"(?<!^)(?<!\.\s)(?<!\?\s)(?<!!\s)\b[A-Z][a-zà-ÿA-Z-]+\b"
        }

    def sanitize(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Remplace les données sensibles par des tokens dans le texte.
        Retourne le texte masqué et le dictionnaire de mapping pour la restauration.
        """
        mapping = {}
        sanitized_text = text
        counters = {key: 1 for key in self.rules.keys()}

        for entity_type, pattern in self.rules.items():
            matches = re.finditer(pattern, sanitized_text)
            # On remplace en partant de la fin pour ne pas décaler les index,
            # mais re.sub avec une fonction est plus simple.
            
            def replacer(match):
                original_value = match.group(0)
                # Si on l'a déjà mappé, on réutilise le token
                existing_token = next((t for t, v in mapping.items() if v == original_value), None)
                if existing_token:
                    return existing_token
                
                token = f"[{entity_type}_{counters[entity_type]}]"
                mapping[token] = original_value
                counters[entity_type] += 1
                return token
                
            sanitized_text = re.sub(pattern, replacer, sanitized_text)

        return sanitized_text, mapping

    def restore(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Restaure les données originales dans le texte généré par le LLM,
        en utilisant le dictionnaire de mapping.
        """
        restored_text = text
        for token, original_value in mapping.items():
            # Remplacement exact du token par sa valeur originale
            restored_text = restored_text.replace(token, original_value)
            
        return restored_text

# Instance Singleton
data_sanitizer = DataSanitizer()
