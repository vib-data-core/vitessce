import './style.css'
import { sign } from './functions.ts'

const searchString = window.location.search;
const urlParams = new URLSearchParams(searchString);
const urlParam = urlParams.get("url");
console.log('URL parameter: ' + urlParam);

document.querySelector<HTMLDivElement>('#app')!.innerHTML = `
  <div>
    <h1>VIB Vitessce</h1>
    <p>Open the console to see the signed request headers.</p>
    <p>URL: ${urlParam}.</p>
    <div id="root"></div>
      <!-- Modal HTML structure -->
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
  </div>
`

// 1. Show the modal to ask for access key, secret key, and bucket
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('modal') as HTMLDivElement;
  const form = document.getElementById('credentialsForm') as HTMLFormElement;

  modal.style.display = 'block';  // Show the modal when the page loads

  // 2. When the form is submitted, get the values and hide the modal
  form.addEventListener('submit', (event) => {
    event.preventDefault();  // Prevent the default form submission

    // Get the values from the form inputs
    const access_key = (document.getElementById('access_key') as HTMLInputElement).value;
    const secret_key = (document.getElementById('secret_key') as HTMLInputElement).value;
    const bucket = (document.getElementById('bucket') as HTMLInputElement).value;

    // Log the values (for debugging)
    console.log('Access Key:', access_key);
    console.log('Secret Key:', secret_key);
    console.log('Bucket:', bucket);

    // Hide the modal after submission
    modal.style.display = 'none';

    // Proceed with your logic using these values
    setupFetch(access_key, secret_key, bucket);
  });
});


// TODO: 1. DO VIB OpenID Connect workflow and get JSON web token (JWT)

// TODO: 2. Get MinIO credentials using JWT. In the meantime we load the credentials from .env

const endpoint = 'https://objectstor.vib.be/'


// 3. Function to setup the Fetch API using the provided credentials
async function setupFetch(access_key: string, secret_key: string, bucket: string) {
  console.log('Access key:', access_key);
  console.log('Secret key:', secret_key);
  console.log('Bucket:', bucket);

  // Now you can use the provided values instead of import.meta.env
  const url = endpoint + bucket;

  const headers = await sign(url); // Assuming you have a sign function to generate the signed headers
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
      const headers = await sign(urlString);
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

// 4. Start Vitessce. A config JSON can be loaded from code or storage (not ideal).
// Nicer would be to just auto config from the Zarr store passed via the URL parameter:
// see https://vitessce.io/docs/default-config-json/

import React from 'react';
import { createRoot } from 'react-dom/client';
import { Vitessce } from 'vitessce';
import { private_config } from './configs.ts'

function MyApp() {
  return React.createElement(
    Vitessce,
    {
      height: 500,
      theme: 'light',
      config: private_config,
    }
  );
}

const container = document.getElementById('root');
if (!container) {
  throw new Error('Root container not found');
}
const root = createRoot(container);
root.render(React.createElement(MyApp));
