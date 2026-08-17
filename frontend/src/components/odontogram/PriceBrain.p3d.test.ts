import { beforeEach, describe, expect, it } from 'vitest';
import { PriceBrain } from './PriceBrain';

describe('P3-D2 PriceBrain pre-archive behavior', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('remembers the latest local price without incrementing usage frequency', () => {
    PriceBrain.recordAct('Composite', 500, 'CONSERVATRICE');
    PriceBrain.recordAct('Composite', 650, 'CONSERVATRICE');

    const history = PriceBrain.getHistory();
    expect(history['brain_Composite']).toMatchObject({
      name: 'Composite',
      price: 650,
      usageCount: 0,
      category: 'CONSERVATRICE',
    });
  });
});
