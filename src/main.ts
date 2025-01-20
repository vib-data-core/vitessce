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
const bucket = 'c01-yvan.saeys-spatial.catalyst'
const url = endpoint + bucket

const headers = await sign(url)
const res = await fetch(url, {
  method: "GET",
  headers: headers
})

const text = await res.text()
console.log(text)

// Intercept fetch requests and apply custom headers, so any fetch request to the endpoint will be signed
window.fetch = new Proxy(window.fetch, {
  apply: async function (target, that, args) {
    // args holds argument of fetch function
    console.log("Normal fetch args: " + args)
    // If url contains some specific string then apply custom headers
    const url = args[0];
    if (url.includes(endpoint)) {
      console.log("Specific string found in url: " + url);
      const headers = await sign(url)
      args[1] = {method: "GET", headers: headers}
    }
    console.log("Custom headers applied: ")
    console.log(args)
    let temp = target.apply(that, args);
    temp.then((res) => {
      // Log the completion of custom fetch request
      console.log("Custom fetch request completed!")
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
import { public_config, private_config } from './configs.ts'

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
const root = createRoot(container);
root.render(React.createElement(MyApp));
