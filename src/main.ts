import './style.css'
import { sign } from './functions.ts'
import React from 'react';
import { createRoot } from 'react-dom/client';
import { Vitessce } from 'vitessce';

const credentials = {
  access_key: '',
  secret_key: '',
  config: '',
};

// TODO: 1. DO VIB OpenID Connect workflow and get JSON web token (JWT)

// TODO: 2. Get MinIO credentials using JWT. In the meantime we load the credentials from .env

const endpoint = 'https://objectstor.vib.be/'

// A utility that *tries* to fetch the config publicly (no signing).
//    If it fails (e.g. 403), we assume it's private and require credentials.
async function tryFetchPublicConfig(bucket: string, pathToConfig: string): Promise<any> {
  const configUrl = `${endpoint}${bucket}/${pathToConfig}`;
  console.log('Attempting public fetch at:', configUrl);

  const res = await fetch(configUrl);
  if (!res.ok) {
    // We throw an error if not 200, so that we can catch it and show the modal
    throw new Error(`Public fetch failed. Status: ${res.status}. Possibly private?`);
  }
  const json = await res.json();
  return json;
}


// A function that intercepts all fetch requests matching `endpoint`
//    and applies AWS-style signing using the user's credentials.
function enableFetchSigning() {
  // Only install the proxy *after* we have credentials from the user:
  window.fetch = new Proxy(window.fetch, {
    apply: async function (target: any, that: any, args: [RequestInfo, RequestInit?]) {
      const url = args[0];
      let urlString: string;

      if (typeof url === 'string') {
        urlString = url;
      } else if (url instanceof Request) {
        urlString = url.url;
      } else {
        throw new Error('Unsupported URL type');
      }

      // If the URL is for the object store, sign it:
      if (urlString.includes(endpoint)) {
        const signedHeaders = await sign(urlString, credentials.access_key, credentials.secret_key);
        // If `args[1]` is missing, create it
        const originalInit = args[1] || {};
        // Merge or overwrite headers
        args[1] = {
          ...originalInit,
          method: 'GET', // or keep originalInit.method if you prefer
          headers: signedHeaders,
        };
      }

      return target.apply(that, args);
    },
  });
}


// Intercept fetch requests and apply custom headers, so any fetch request to the endpoint will be signed
window.fetch = new Proxy(window.fetch, {
  apply: async function (target: any, that: any, args: [RequestInfo, RequestInit?]) {
    console.log("Normal fetch args:", args);

    const url = args[0];
    let urlString: string;

    // Check if url is a string or Request and extract the URL accordingly
    if (typeof url === 'string') {
      urlString = url; // Directly use the string URL
    } else if (url instanceof Request) {
      urlString = url.url; // Extract the URL from the Request object
    } else {
      throw new Error('Unsupported URL type');
    }

    // If url contains the endpoint, apply custom headers
    if (urlString.includes(endpoint)) {
      console.log("Specific string found in url: " + urlString);
      const headers = await sign(urlString, credentials.access_key, credentials.secret_key);
      args[1] = { method: "GET", headers: headers }; // Apply custom headers
    }

    console.log("Custom headers applied:", args);
    const temp = target.apply(that, args); // Call the original fetch
    temp.then(() => {
      console.log("Custom fetch request completed!");
    });
    return temp;
  },
});

// A helper to fetch the config from the bucket
async function fetchConfig(bucket: string, path_to_config: string): Promise<any> {
  const configUrl = `${endpoint}${bucket}/${path_to_config}`;
  console.log('Fetching config from:', configUrl);

  const res = await fetch(configUrl);
  const config = await res.json();
  return config;
}


// Define a function to render Vitessce *after* we have credentials and config
function initializeVitessce(config: any ) {
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

// Setup UI
const searchString = window.location.search;
const urlParams = new URLSearchParams(searchString);
const urlParam = urlParams.get("url");

console.log('URL parameter: ' + urlParam);

// Put the HTML in the page
document.querySelector<HTMLDivElement>('#app')!.innerHTML = `
  <div>
    <h1>VIB Vitessce</h1>
    <p>Open the console to see the signed request headers.</p>
    <p>URL: ${urlParam}.</p>
    <div id="root"></div>
    <div id="modal" class="modal">
      <div class="modal-content">
        <h2>Enter Credentials</h2>
        <form id="credentialsForm">
          <label for="access_key">Access Key:</label>
          <input type="text" id="access_key" name="access_key" required><br><br>
          
          <label for="secret_key">Secret Key:</label>
          <input type="text" id="secret_key" name="secret_key" required><br><br>
          
          <label for="config">Location:</label>
          <input type="text" id="config" name="config" required><br><br>

          <button type="submit">Submit</button>
        </form>
      </div>
    </div>
  </div>
`;


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
    console.log('Config:', credentials.config);

    // Hide the modal
    hideModal();

    // Enable fetch signing now that we have credentials
    enableFetchSigning();

    // Parse bucket + path from the config input
    const [bucket, ...pathParts] = credentials.config.split('/');
    const pathToConfig = pathParts.join('/');

    // Attempt to fetch the config with credentials
    let signedConfig: any;
    try {
      signedConfig = await fetchConfig(bucket, pathToConfig);
      console.log('Fetched config (signed):', signedConfig);
    } catch (e) {
      console.error('Error fetching config with signing:', e);
      alert('Error fetching config with signing. Check the console for details.');
      return;
    }

    // Initialize Vitessce
    initializeVitessce(signedConfig);
  });
});

// Attempt a "public" load right away. If it fails, show the modal.
(async function main() {
  // For example, read ?url=bucket/path_to_config.json from the query string
  const searchString = window.location.search;
  const urlParams = new URLSearchParams(searchString);
  const urlParam = urlParams.get("url");  // e.g. "my-public-bucket/my-config.json"

  if (!urlParam) {
    // If there's no ?url=... parameter, we have no location to test.
    // So just show the modal right away:
    console.log( "No ?url= parameter found. Assuming private bucket." )
    showModal();
    return;
  }

  // We have a config path from the URL, so let's try it publicly:
  const [bucket, ...pathParts] = urlParam.split('/');
  const pathToConfig = pathParts.join('/');

  try {
    const publicConfig = await tryFetchPublicConfig(bucket, pathToConfig);
    console.log('Successfully fetched config publicly:', publicConfig);
    // If successful, initialize Vitessce with the public config:
    initializeVitessce(publicConfig);
  } catch (error) {
    console.warn('Public fetch failed, showing modal for credentials...');
    showModal();
  }
})();
