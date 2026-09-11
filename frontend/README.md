# WeatherGPT — React Frontend

A weather app where an AI chat assistant is the centerpiece. Built to an
"atmospheric instrument panel" design system: Fraunces for display type,
Space Grotesk for UI, IBM Plex Mono for data readouts, a terracotta accent
on a near-black ink palette, sharp-edged data cards, and soft-edged chat.

## Run it

```bash
npm install
npm run dev
```

Opens at http://localhost:5173. The app talks to the real Django backend
at `http://localhost:8000` by default — the full documented API (weather,
forecast, hourly, compare, alerts, chat, conversations, favorites) is
served live. No backend running? Launch the standalone demo with
`VITE_MOCK=true npm run dev`, which simulates the whole API with
realistic data and network delay.

## Connecting the real Django backend

**Already connected.** `src/api/client.js` defaults to the real backend:

```js
export const MOCK_MODE = import.meta.env.VITE_MOCK === "true";
```

1. Make sure your Django server is running at `http://localhost:8000`
   (or set `VITE_API_PROXY_TARGET` before running `npm run dev`).
2. `npm run dev` — every resource module in `src/api/` calls the exact
   endpoint shapes from the API spec served by the backend.
3. Standalone demo (no backend needed): `VITE_MOCK=true npm run dev`.

## Structure

```
src/
  api/          client.js (fetch wrapper + error envelope), mock.js
                (simulated backend), weather.js, chat.js, alerts.js,
                conversations.js, favorites.js — one module per resource
  hooks/        useFetch, useWeather, useChat, useFavorites
  components/   LocationSearch, CurrentWeather, Forecast, Hourly, Alerts,
                ChatWindow/ChatMessage/ChatInput/TypingIndicator,
                AnimatedNumber, Icons (custom SVG set), Nav
  pages/        Dashboard, ComparePage, ConversationsPage, FavoritesPage
  styles/       tokens.css (design system), global.css, app.css
```

## Design notes

- No router — page switching is a small `useState` in `App.jsx`, per the
  "don't add a router unless strictly needed" constraint.
- No UI kit — plain CSS driven entirely by the custom properties in
  `tokens.css`.
- Every async section (current weather, forecast, hourly, alerts, chat,
  conversations, favorites) implements idle/loading/success/error and
  never crashes the page on failure.
- Metric/imperial toggle in the nav updates every number across every
  page at once.
- `prefers-reduced-motion` is respected globally (see `tokens.css` and
  `global.css`) — animations collapse to near-instant, opacity-only
  transitions.
