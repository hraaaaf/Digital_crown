import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { chromium, request } from 'playwright';
import { enrollT2Workstation } from './t2-workstation-session.mjs';

const target = process.argv[2];
const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!target) throw new Error('Target script path is required');
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const bootstrap = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await bootstrap.post('/api/auth/login', {
  form: { username: user, password },
});
if (!login.ok()) {
  throw new Error(`T2 workstation bootstrap login failed: ${login.status()} ${await login.text()}`);
}
const tokens = await login.json();
const workstationStorage = await enrollT2Workstation(bootstrap, tokens.access_token, password);

const mobilePairingToken = process.env.T2_MOBILE_PAIRING_TOKEN;
if (mobilePairingToken) {
  const ecdh = crypto.createECDH('prime256v1');
  ecdh.generateKeys();
  const mobileClaim = await bootstrap.post('/api/mobile/claim-token', {
    data: {
      token: mobilePairingToken,
      client_public_key_hex: ecdh.getPublicKey('hex', 'uncompressed'),
    },
  });
  if (!mobileClaim.ok()) {
    throw new Error(`T2 mobile bootstrap failed: ${mobileClaim.status()}`);
  }
  const mobileTokens = await mobileClaim.json();
  process.env.T2_MOBILE_ACCESS_TOKEN = mobileTokens.access_token;
}
await bootstrap.dispose();

const originalRequestNewContext = request.newContext.bind(request);
request.newContext = async (options = {}) => originalRequestNewContext({
  ...options,
  storageState: options.storageState ?? workstationStorage,
});

const originalLaunch = chromium.launch.bind(chromium);
chromium.launch = async (...args) => {
  const browser = await originalLaunch(...args);
  const originalBrowserNewContext = browser.newContext.bind(browser);
  browser.newContext = async (options = {}) => originalBrowserNewContext({
    ...options,
    storageState: options.storageState ?? workstationStorage,
  });
  return browser;
};

await import(pathToFileURL(path.resolve(target)).href);
