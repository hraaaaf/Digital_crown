import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { DayOneTour } from './DayOneTour';

describe('DayOneTour T1 neutralization', () => {
  it('renders nothing so returning to Dashboard cannot auto-open a tour', () => {
    expect(renderToStaticMarkup(<DayOneTour />)).toBe('');
  });
});
