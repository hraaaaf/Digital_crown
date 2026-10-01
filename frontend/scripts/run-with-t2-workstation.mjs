import path from 'node:path';
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
