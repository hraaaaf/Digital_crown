import React from 'react';
import { AppLoader } from './AppLoader';

interface DigitalCrownLoaderProps {
  text?: string;
  minHeight?: string;
  textColor?: string;
  spinnerColor?: string;
  className?: string;
}

export const DigitalCrownLoader: React.FC<DigitalCrownLoaderProps> = ({ 
  text, 
  minHeight,
  className
}) => {
  return <AppLoader text={text} minHeight={minHeight} className={className} />;
};
