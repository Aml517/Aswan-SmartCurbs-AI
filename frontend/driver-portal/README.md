# Aswan SmartCurbs AI — Driver Portal

Driver/User web portal for the **Aswan SmartCurbs AI** smart parking management
graduation project. This repo covers only the **Driver Portal** (login, zone
browsing, zone details, reservations). Vehicle detection is owned by the AI
team, live data will be served by the Backend team's FastAPI service, and the
Municipality Dashboard is a separate codebase owned by another teammate.

## Tech stack

- React 18 + Vite
- React Router DOM (client-side routing + route protection)
- Axios (pre-wired API client, currently backed by mock data)
- Plain CSS with a shared design-token file (`src/styles/variables.css`)

## Getting started

```bash
npm install
npm run dev
```

The app runs at `http://localhost:5173`. Login is the default route — enter
any email and password (fake auth) to reach the portal.

```bash
npm run build     # production build
npm run preview   # preview the production build locally
```

## Routes

| Path                    | Page            | Access        |
| ------------------------ | --------------- | ------------- |
| `/`                      | Redirects to `/login` | Public |
| `/login`                 | Login            | Public        |
| `/parking-zones`         | Parking Zones list | Protected  |
| `/parking-zones/:id`     | Parking Zone details | Protected |
| `/reservation`           | Reservation form | Protected     |

Protected routes are wrapped in `src/components/ProtectedRoute.jsx`, which
checks for a `driverEmail` key in `localStorage` (set by `Login.jsx` after a
successful — currently fake — sign-in) and redirects unauthenticated visitors
back to `/login`.

## Project structure

```
src/
├── components/
│   ├── Navbar.jsx / .css
│   ├── ParkingCard.jsx / .css
│   ├── Loading.jsx / .css
│   ├── EmptyState.jsx / .css
│   └── ProtectedRoute.jsx
├── pages/
│   ├── Login.jsx / .css
│   ├── ParkingZones.jsx / .css
│   ├── ParkingDetails.jsx / .css
│   └── Reservation.jsx / .css
├── services/
│   └── api.js
├── data/
│   └── mockData.js
├── styles/
│   ├── global.css
│   └── variables.css
├── App.jsx
└── main.jsx
```

## Connecting to the real FastAPI backend

The Driver Portal is wired to the real backend by default — no mock data
unless you opt in. All data access goes through `src/services/api.js`,
which calls these live endpoints (see `backend/app/api/v1/*.py`):

| Frontend function | Backend endpoint |
| --- | --- |
| `getParkingZones()` | `GET /api/v1/availability` |
| `getParkingZoneById(id)` | `GET /api/v1/zones/{id}` |
| `getParkingAvailability(id)` | `GET /api/v1/availability/{id}` (includes per-space status) |
| `createReservation({ spaceId, driverName, plateNumber })` | `POST /api/v1/reservations` with `{ space_id, driver_name, vehicle_plate }` |

Reservations are made against a **specific parking space**, not just a zone —
`ParkingDetails` lets the driver pick one of the currently-available spaces
before continuing to the reservation form, which also collects the driver's
full name (`driver_name` is required by the backend).

### Configuration

By default the app points at `http://localhost:8000/api/v1`. Override this,
or switch to mock data, with a `.env` file in the project root:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_USE_MOCK_DATA=false   # set to "true" to demo without the backend running
```

### ⚠️ CORS must be enabled on the backend

`backend/app/main.py` does not currently allow cross-origin requests, so the
browser will block every call from `localhost:5173` until this is added:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Seeding demo data

The database starts empty. Before a demo, use the backend's Swagger UI
(`http://localhost:8000/docs`) to create a few zones (`POST /api/v1/zones`)
and spaces (`POST /api/v1/zones/{zone_id}/spaces`) so the portal has
something to show.

## Notes

- Authentication is intentionally fake for this milestone: any non-empty
  email/password combination signs the driver in and stores their email in
  `localStorage`.
- The Municipality Dashboard is **not** part of this repository.
