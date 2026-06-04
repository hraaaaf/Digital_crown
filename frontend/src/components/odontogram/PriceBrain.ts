/**
 * PriceBrain.ts
 * Gère la mémoire des tarifs et de la fréquence des actes (Brain Ghost)
 */

export interface ActHistory {
  id: string;
  name: string;
  price: number;
  usageCount: number;
  category: string;
  duration?: number;
  scope?: string;
}

const STORAGE_KEY = 'ghost_act_brain';

export const PriceBrain = {
  /**
   * Récupère l'historique complet
   */
  getHistory: (): Record<string, ActHistory> => {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : {};
    } catch {
      return {};
    }
  },

  /**
   * Enregistre un acte (met à jour le prix et incrémente l'usage)
   */
  recordAct: (name: string, price: number, category: string, id?: string) => {
    const history = PriceBrain.getHistory();
    const actId = id || `brain_${name}`;
    const existing = history[actId] || { id: actId, name, price: 0, usageCount: 0, category };
    
    history[actId] = {
      ...existing,
      price: price, // On retient le dernier prix saisi
      usageCount: existing.usageCount + 1,
      category: category,
      name: name // On s'assure que le nom est à jour
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  },

  /**
   * Récupère le Top N des actes les plus fréquents
   */
  getTopFrequent: (limit: number = 7): ActHistory[] => {
    const history = PriceBrain.getHistory();
    return Object.values(history)
      .sort((a, b) => b.usageCount - a.usageCount)
      .slice(0, limit);
  },

  /**
   * Suggère un prix pour un acte donné
   */
  suggestPrice: (name: string): number | null => {
    const history = PriceBrain.getHistory();
    return history[name]?.price || null;
  },

  /**
   * Enregistre un schéma d'échelonnement type
   */
  recordInstallmentPlan: (title: string, advance: number, months: number, monthly: number) => {
    try {
      const data = localStorage.getItem('ghost_installment_brain');
      const history = data ? JSON.parse(data) : {};
      history[title.toLowerCase()] = { advance, months, monthly, lastUsed: Date.now() };
      localStorage.setItem('ghost_installment_brain', JSON.stringify(history));
    } catch (e) {}
  },

  /**
   * Suggère un schéma d'échelonnement basé sur le titre
   */
  suggestInstallmentPlan: (title: string): { advance: number, months: number, monthly: number } | null => {
    try {
      const data = localStorage.getItem('ghost_installment_brain');
      if (!data) return null;
      const history = JSON.parse(data);
      const exactMatch = history[title.toLowerCase()];
      if (exactMatch) return exactMatch;
      
      // Recherche partielle
      for (const [key, plan] of Object.entries(history)) {
        if (title.toLowerCase().includes(key) || key.includes(title.toLowerCase())) {
          return plan as { advance: number, months: number, monthly: number };
        }
      }
    } catch (e) {}
    return null;
  }
};
