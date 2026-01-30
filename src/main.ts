import './style.css'
import { sign } from './functions.ts'
import React from 'react';
import { createRoot } from 'react-dom/client';
import { Vitessce } from 'vitessce';

// Store credentials from user input:
const credentials = {
  access_key: '',
  secret_key: '',
  config: '',
};

// Your MinIO/S3 endpoint:
const endpoint = 'https://objectstor.vib.be/';
// Backend url for serving local files (proxied by Vite in dev)
const localConfigEndpoint = '/api/config';

// Attempt a PUBLIC fetch first, with the real/original fetch (unproxied).
async function tryFetchPublicConfig(bucket: string, pathToConfig: string) {
  const configUrl = `${endpoint}${bucket}/${pathToConfig}`;
  console.log('Attempting public fetch at:', configUrl);

  return fetchConfigByUrl(configUrl, 'Public fetch');
}

// Only AFTER we confirm we need credentials do we install the fetch proxy.
function enableFetchSigning() {
  console.log('Enabling fetch signing with user credentials...');

  window.fetch = new Proxy(window.fetch, {
    apply: async function (target, that, args) {
      let urlString;
      const [url, init] = args;

      if (typeof url === 'string') {
        urlString = url;
      } else if (url instanceof Request) {
        urlString = url.url;
      } else {
        throw new Error('Unsupported URL type');
      }

      // Only sign requests that go to the object store and only if we have real credentials
      if (
        urlString.includes(endpoint) &&
        credentials.access_key !== '' &&
        credentials.secret_key !== ''
      ) {
        console.log("Signing request:", urlString);
        const signedHeaders = await sign(urlString, credentials.access_key, credentials.secret_key);
        args[1] = {
          ...init,
          method: 'GET',  // or preserve init.method if you have other request types
          headers: signedHeaders,
        };
      }

      // Forward the request to the original fetch
      return target.apply(that, args as [RequestInfo, RequestInit?]);
    },
  });
}

// A helper to fetch a config (this time presumably with signing, if installed).
async function fetchConfig(bucket: string, pathToConfig: string) {
  const configUrl = `${endpoint}${bucket}/${pathToConfig}`;
  console.log('Fetching config from:', configUrl);

  return fetchConfigByUrl(configUrl, 'Signed fetch');
}

function isHttpUrl(value: string) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

function absolutizeUrl(value: string) {
  if (isHttpUrl(value)) {
    return value;
  }
  if (value.startsWith('/')) {
    return new URL(value, window.location.origin).href;
  }
  return value;
}

function normalizeConfigUrls(config: any) {
  if (!config || typeof config !== 'object') {
    return config;
  }
  if (Array.isArray(config)) {
    config.forEach(normalizeConfigUrls);
    return config;
  }

  Object.entries(config).forEach(([key, value]) => {
    if (key === 'url' && typeof value === 'string') {
      config[key] = absolutizeUrl(value);
      return;
    }
    normalizeConfigUrls(value);
  });

  return config;
}

async function fetchConfigByUrl(configUrl: string, label = 'Fetch') {
  console.log(`${label} at:`, configUrl);
  const res = await fetch(configUrl);
  if (!res.ok) {
    throw new Error(`${label} failed with status ${res.status}`);
  }
  return res.json();
}

async function fetchLocalConfig(filePath: string) {
  const configUrl = `${localConfigEndpoint}?path=${encodeURIComponent(filePath)}`;
  return fetchConfigByUrl(configUrl, 'Local config fetch');
}

// Render Vitessce after we have a config
function initializeVitessce(config: any) {
  const container = document.getElementById('root');
  if (!container) {
    throw new Error('Root container not found');
  }
  const root = createRoot(container);

  function MyApp() {
    return React.createElement(Vitessce, {
      height: 500,
      theme: 'light',
      config: config,
    });
  }

  root.render(React.createElement(MyApp));
}

// Insert minimal HTML UI + a modal for credentials
document.querySelector<HTMLDivElement>('#app')!.innerHTML = `
  <div>
    <img src="/vitessce/VIBRGBnotaglinepos.png" alt="VIB Vitessce Logo" style="width: 150px; height: auto;">
    <div id="root"></div>
    <div id="modal" class="modal" style="display:none; position:fixed; 
         top:50%; left:50%; transform:translate(-50%, -50%); background:#eee; padding:20px;">
      <div class="modal-content">
        <h2>Enter Credentials</h2>
        <form id="credentialsForm">
          <label for="access_key">Access Key:</label>
          <input type="text" id="access_key" name="access_key" required><br><br>

          <label for="secret_key">Secret Key:</label>
          <input type="password" id="secret_key" name="secret_key" required><br><br>

          <label for="config">Location (bucket/path.json, /data/groups/... or https://...):</label>
          <input type="text" id="config" name="config" required><br><br>

          <button type="submit">Submit</button>
        </form>
      </div>
    </div>
  </div>

`;

// Modal helpers
function showModal() {
  const modal = document.getElementById('modal') as HTMLDivElement;
  modal.style.display = 'block';
}

function hideModal() {
  const modal = document.getElementById('modal') as HTMLDivElement;
  modal.style.display = 'none';
}

// Handle user form submission for credentials
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('credentialsForm') as HTMLFormElement;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // Grab user inputs
    credentials.access_key = (document.getElementById('access_key') as HTMLInputElement).value;
    credentials.secret_key = (document.getElementById('secret_key') as HTMLInputElement).value;
    credentials.config = (document.getElementById('config') as HTMLInputElement).value;

    //console.log('Access Key:', credentials.access_key);
    //console.log('Secret Key:', credentials.secret_key);
    //console.log('Config (bucket/path):', credentials.config);

    // Hide the modal
    hideModal();

    //“Fetch the config (sign if needed)”
    let signedConfig;
    try {
      const input = credentials.config.trim();
      if (isHttpUrl(input)) {
        if (input.includes(endpoint)) {
          enableFetchSigning();
        }
        signedConfig = await fetchConfigByUrl(input, 'Config fetch');
      } else if (input.startsWith('/')) {
        signedConfig = await fetchLocalConfig(input);
      } else {
        // Enable fetch signing now that we have credentials
        enableFetchSigning();
        // Parse bucket + path from the config input
        const [bucket, ...pathParts] = input.split('/');
        const pathToConfig = pathParts.join('/');
        signedConfig = await fetchConfig(bucket, pathToConfig);
      }
      console.log('Fetched config:', signedConfig);
    } catch (e) {
      console.error('Error fetching config with signing:', e);
      alert('Error fetching config with signing. Check console for details.');
      return;
    }

    // Initialize Vitessce with the newly fetched config
    initializeVitessce(normalizeConfigUrls(signedConfig));
  });
});

// Main logic: try public fetch from ?url=... first, fallback to modal if 403
(async function main() {
  const searchString = window.location.search;
  const urlParams = new URLSearchParams(searchString);
  const urlParam = urlParams.get("url");
  const fileParam = urlParams.get("file");
  // e.g. ?url=my-public-bucket/my-config.json or ?url=https://... or ?file=/data/groups/.../config.json

  if (urlParam) {
    try {
      if (isHttpUrl(urlParam)) {
        const publicConfig = await fetchConfigByUrl(urlParam, 'URL fetch');
        console.log('Successfully fetched config by URL:', publicConfig);
        initializeVitessce(normalizeConfigUrls(publicConfig));
        return;
      }

      // Attempt a public fetch for object store bucket/path
      const [bucket, ...pathParts] = urlParam.split('/');
      const pathToConfig = pathParts.join('/');
      const publicConfig = await tryFetchPublicConfig(bucket, pathToConfig);
      console.log('Successfully fetched config publicly:', publicConfig);
      initializeVitessce(normalizeConfigUrls(publicConfig));
      return;
    } catch (err) {
      console.warn('URL fetch failed or is forbidden, prompting for credentials...', err);
      showModal();
      return;
    }
  }

  if (fileParam) {
    try {
      const publicConfig = await fetchLocalConfig(fileParam);
      console.log('Successfully fetched config from local backend:', publicConfig);
      initializeVitessce(normalizeConfigUrls(publicConfig));
      return;
    } catch (err) {
      console.warn('Local file fetch failed, prompting for credentials...', err);
      showModal();
      return;
    }
  }

  console.log("No ?url= or ?file= parameter found. Assuming private bucket, show credentials modal.");
  showModal();
})();
