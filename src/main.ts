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

// Attempt a PUBLIC fetch first, with the real/original fetch (unproxied).
async function tryFetchPublicConfig(bucket: string, pathToConfig: string) {
  const configUrl = `${endpoint}${bucket}/${pathToConfig}`;
  console.log('Attempting public fetch at:', configUrl);

  const res = await fetch(configUrl);
  if (!res.ok) {
    // Throw an error so we can catch it and show the modal
    throw new Error(`Public fetch failed. Status: ${res.status}. Possibly private?`);
  }
  const json = await res.json();
  return json;
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

  const res = await fetch(configUrl);
  if (!res.ok) {
    throw new Error(`Fetch for config failed with status ${res.status}`);
  }
  const config = await res.json();
  return config;
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

          <label for="config">Location (bucket/path.json):</label>
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

    console.log('Access Key:', credentials.access_key);
    console.log('Secret Key:', credentials.secret_key);
    console.log('Config (bucket/path):', credentials.config);

    // Hide the modal
    hideModal();

    // Enable fetch signing now that we have credentials
    enableFetchSigning();

    // Parse bucket + path from the config input
    const [bucket, ...pathParts] = credentials.config.split('/');
    const pathToConfig = pathParts.join('/');

    // Now fetch the config *with signing*
    let signedConfig;
    try {
      signedConfig = await fetchConfig(bucket, pathToConfig);
      console.log('Fetched config (signed):', signedConfig);
    } catch (e) {
      console.error('Error fetching config with signing:', e);
      alert('Error fetching config with signing. Check console for details.');
      return;
    }

    // Initialize Vitessce with the newly fetched config
    initializeVitessce(signedConfig);
  });
});

// Main logic: try public fetch from ?url=... first, fallback to modal if 403
(async function main() {
  const searchString = window.location.search;
  const urlParams = new URLSearchParams(searchString);
  const urlParam = urlParams.get("url"); 
  // e.g. ?url=my-public-bucket/my-config.json

  if (!urlParam) {
    console.log("No ?url= parameter found. Assuming private bucket, show credentials modal.");
    showModal();
    return;
  }

  // Attempt a public fetch
  const [bucket, ...pathParts] = urlParam.split('/');
  const pathToConfig = pathParts.join('/');

  try {
    const publicConfig = await tryFetchPublicConfig(bucket, pathToConfig);
    console.log('Successfully fetched config publicly:', publicConfig);
    // If we got here, the data is publicly available. Render Vitessce:
    initializeVitessce(publicConfig);
  } catch (err) {
    console.warn('Public fetch failed or is forbidden, prompting for credentials...', err);
    showModal();
  }
})();
