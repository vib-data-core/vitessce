import './style.css'
import { sign } from './functions.ts'
import React from 'react';
import { createRoot } from 'react-dom/client';
import { Vitessce } from 'vitessce';
import { private_config } from './configs.ts'


const credentials = {
  access_key: '',
  secret_key: '',
  bucket: '',
};


// TODO: 1. DO VIB OpenID Connect workflow and get JSON web token (JWT)

// TODO: 2. Get MinIO credentials using JWT. In the meantime we load the credentials from .env

const endpoint = 'https://objectstor.vib.be/'


// Function to setup the Fetch API using the provided credentials
async function setupFetch(access_key: string, secret_key: string, bucket: string) {
  // Now you can use the provided values instead of import.meta.env
  const url = endpoint + bucket;

  const headers = await sign(url, access_key, secret_key);
  const res = await fetch(url, {
    method: 'GET',
    headers: headers,
  });

  const text = await res.text();
  console.log(text);
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


// Define a function to render Vitessce *after* we have credentials
function initializeVitessce() {
  const container = document.getElementById('root');
  if (!container) {
    throw new Error('Root container not found');
  }
  const root = createRoot(container);

  function MyApp() {
    return React.createElement(Vitessce, {
      height: 500,
      theme: 'light',
      config: private_config,
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
          
          <label for="bucket">Bucket:</label>
          <input type="text" id="bucket" name="bucket" required><br><br>

          <button type="submit">Submit</button>
        </form>
      </div>
    </div>
  </div>
`;

// Show the modal + handle form submission
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('modal') as HTMLDivElement;
  const form = document.getElementById('credentialsForm') as HTMLFormElement;

  modal.style.display = 'block';  // Show the modal when the page loads

  form.addEventListener('submit', async (event) => {
    event.preventDefault(); 

    // Grab user inputs
    credentials.access_key = (document.getElementById('access_key') as HTMLInputElement).value;
    credentials.secret_key = (document.getElementById('secret_key') as HTMLInputElement).value;
    credentials.bucket = (document.getElementById('bucket') as HTMLInputElement).value;

    // Debug
    console.log('Access Key:', credentials.access_key);
    console.log('Secret Key:', credentials.secret_key);
    console.log('Bucket:', credentials.bucket);

    // Hide the modal
    modal.style.display = 'none';

    // Proceed with logic
    await setupFetch(credentials.access_key, credentials.secret_key, credentials.bucket);

    // Now that credentials are available, we can safely initialize Vitessce
    initializeVitessce();
  });
});



