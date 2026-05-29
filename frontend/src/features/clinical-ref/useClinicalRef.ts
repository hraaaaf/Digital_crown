import { useState, useEffect } from 'react';
import type { ClinicalProtocol } from './types';
import { getProtocolByActName } from '../../data/clinical-protocols';

export const useClinicalRef = (actName?: string) => {
  const [protocol, setProtocol] = useState<ClinicalProtocol | undefined>(undefined);

  useEffect(() => {
    if (actName) {
      const found = getProtocolByActName(actName);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setProtocol(found);
    } else {
       
      setProtocol(undefined);
    }
  }, [actName]);

  return protocol;
};
