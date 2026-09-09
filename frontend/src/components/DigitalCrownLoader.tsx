import React from 'react';
import { AppLoader } from './AppLoader';

interface DigitalCrownLoaderProps {
  text?: string;
  minHeight?: string;
  textColor?: string;
  spinnerColor?: string;
  className?: string;
}

const legacyStartupCopy = "Patientez pendant le démarrage de l'IA...";

export const DigitalCrownLoader: React.FC<DigitalCrownLoaderProps> = ({
  text,
  minHeight,
  className,
}) => {
  const truthfulText = text === legacyStartupCopy ? 'Démarrage de Digital Crown...' : text;
  return <AppLoader text={truthfulText} minHeight={minHeight} className={className} />;
};
