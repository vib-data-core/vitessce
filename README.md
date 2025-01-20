# Vitessce using Project Storage

## Installation

- Open this folder in your terminal
- Install npm

```
npm install
npm install -D vite
```

Get your credentials from objectstor.vib.be and store them in an `.env` file in the root of the project.

```
VITE_ACCESS_KEY=123
VITE_SECRET_KEY=abc
```

Run the project
```
npm run dev
```

Open your browser and look at the console log. The Vitessce UI should load and show the data from the object store  in bucket `spatial-hackathon-private/`.

![Vitessce UI](./public/Screenshot%202024-09-18%20at%2023.06.16.png)
