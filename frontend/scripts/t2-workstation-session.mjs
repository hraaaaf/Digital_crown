export async function enrollT2Workstation(api, accessToken, accountPassword) {
  const response = await api.post('/api/workstation/enroll', {
    data: { accountPassword },
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok()) {
    throw new Error(`Workstation enrollment failed: ${response.status()} ${await response.text()}`);
  }
  return api.storageState();
}
