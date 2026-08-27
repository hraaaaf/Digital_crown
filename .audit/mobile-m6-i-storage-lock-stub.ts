export const MobileStorage = {
  async getBiometricVaultEnvelope() { return { credential_id: 'visual-credential', prf_salt: 'visual-salt' }; },
  async isBiometricVaultUnlocked() { return false; },
  getBiometricAccessToken() { return null; },
  lockBiometricVault() {},
};
