export type Density = 'compact' | 'confort' | 'etendu';
export type Scope = 'app' | 'doc';

export type Preset = {
  id: string;
  name: string;
  vibe: string;
  palette: string;   
  font: string;      
  template: string;  
  appTheme: string;  
  density: Density;
};
