/**
 * PriceBrain.ts
 * Mémoire locale des tarifs. La fréquence d'usage clinique est autoritative côté
 * backend après archivage réussi d'un document financier.
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

let _historyCache: Record<string, ActHistory> | null = null;

export const PriceBrain = {
  /**
   * Récupère l'historique complet (en mémoire cache, invalidé à chaque écriture).
   */
  getHistory: (): Record<string, ActHistory> => {
    if (_historyCache) return _historyCache;
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      _historyCache = data ? JSON.parse(data) : {};
      return _historyCache!;
    } catch {
      return {};
    }
  },

  /**
   * Mémorise le dernier prix saisi localement sans incrémenter la fréquence.
   *
   * P3-D2 : sélectionner, éditer ou confirmer un acte n'est pas une preuve
   * d'utilisation clinique. `usageCount` est donc conservé tel quel. La fréquence
   * autoritative est enregistrée côté backend après archivage réussi.
   */
  recordAct: (name: string, price: number, category: string, id?: string) => {
    const history = PriceBrain.getHistory();
    const actId = id || `brain_${name}`;
    const existing = history[actId] || { id: actId, name, price: 0, usageCount: 0, category };

    history[actId] = {
      ...existing,
      price,
      usageCount: existing.usageCount,
      category,
      name,
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    _historyCache = null;
  },

  /**
   * Récupère le Top N local historique. Les nouveaux événements P3 ne modifient
   * plus ce compteur avant archivage.
   */
  getTopFrequent: (limit: number = 7): ActHistory[] => {
    const history = PriceBrain.getHistory();
    return Object.values(history)
      .sort((a, b) => b.usageCount - a.usageCount)
      .slice(0, limit);
  },

  /**
   * Suggère un prix pour un acte donné.
   */
  suggestPrice: (name: string): number | null => {
    const history = PriceBrain.getHistory();
    return history[`brain_${name}`]?.price ?? history[name]?.price ?? null;
  },

  /**
   * Enregistre un schéma d'échelonnement type.
   */
  recordInstallmentPlan: (title: string, advance: number, months: number, monthly: number) => {
    try {
      const data = localStorage.getItem('ghost_installment_brain');
      const history = data ? JSON.parse(data) : {};
      history[title.toLowerCase()] = { advance, months, monthly, lastUsed: Date.now() };
      localStorage.setItem('ghost_installment_brain', JSON.stringify(history));
    } catch (e) {
      console.warn('PriceBrain: failed to record installment plan', e);
    }
  },

  /**
   * Suggère un schéma d'échelonnement basé sur le titre.
   */
  suggestInstallmentPlan: (title: string): { advance: number, months: number, monthly: number } | null => {
    try {
      const data = localStorage.getItem('ghost_installment_brain');
      if (!data) return null;
      const history = JSON.parse(data);
      const exactMatch = history[title.toLowerCase()];
      if (exactMatch) return exactMatch;

      for (const [key, plan] of Object.entries(history)) {
        if (title.toLowerCase().includes(key) || key.includes(title.toLowerCase())) {
          return plan as { advance: number; months: number; monthly: number };
        }
      }
    } catch (e) {
      console.warn('PriceBrain: failed to suggest installment plan', e);
    }
    return null;
  },
};
