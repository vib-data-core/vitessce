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
  </div>
`
// TODO: 1. DO VIB OpenID Connect workflow and get JSON web token (JWT)

// TODO: 2. Get MinIO credentials using JWT. In the meantime we load the credentials from .env

const endpoint = 'https://objectstor.vib.be/'
const access_key = import.meta.env.VITE_ACCESS_KEY
const secret_key = import.meta.env.VITE_SECRET_KEY 

console.log(access_key)
console.log(secret_key)

// 3. Setup the Fetch API with signed S3 credentials.
// This is just some example code to fetch a file from MinIO
async function fetchData() {
  const bucket = "c01-yvan.saeys-spatial.catalyst";
  const url = endpoint + bucket;
  const headers = await sign(url);  // Now inside async function
  const res = await fetch(url, {
    method: "GET",
    headers: headers
  });

  const text = await res.text();
  console.log(text);
}

fetchData();

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