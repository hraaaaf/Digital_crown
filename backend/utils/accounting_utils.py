
def extract_amount_from_clinical_data(clinical_data: dict) -> float:
    """
    Extrait de manière robuste le montant total d'un document à partir de ses données cliniques.
    Gère les anciens et nouveaux formats (Ghost Elite v4.x).
    """
    if not clinical_data:
        return 0.0
    
    # 1. Priorité au champ 'total' ou 'total_amount' explicite
    for key in ['total_amount', 'total', 'amount', 'montant_total']:
        if key in clinical_data:
            try:
                val = float(clinical_data[key])
                if val > 0: return val
            except (ValueError, TypeError):
                continue

    # 2. Somme des 'payments' (Note d'honoraires)
    if 'payments' in clinical_data and isinstance(clinical_data['payments'], list):
        try:
            total = sum(float(p.get('montant', p.get('amount', p.get('prix', 0)))) for p in clinical_data['payments'])
            if total > 0: return total
        except (ValueError, TypeError):
            pass

    # 3. Somme des 'items' (Devis)
    if 'items' in clinical_data and isinstance(clinical_data['items'], list):
        try:
            total = sum(float(i.get('prix_unitaire', i.get('montant', i.get('price', 0)))) for i in clinical_data['items'])
            if total > 0: return total
        except (ValueError, TypeError):
            pass
            
    # 4. Fallback sur 'prix' (Vieux formats)
    if 'prix' in clinical_data:
        try:
            return float(clinical_data['prix'])
        except (ValueError, TypeError):
            pass

    return 0.0
