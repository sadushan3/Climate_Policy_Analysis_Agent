# Frontend (Vite + React)

## Dev
```bash
npm install
npm run dev
```

The UI will call `http://localhost:8000/api/recommendations/` by default.  
To change the API base, create `.env`:

```
VITE_API_BASE=http://127.0.0.1:8000
```

## Build
```bash
npm run build
npm run preview
```