// seat-check/components/MapView.web.tsx
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useState, useCallback } from "react";
import { API, fetchJSON } from "@/constants/api";

type Feature = {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] }; // [lon, lat]
  properties: {
    id: number;
    name: string;
    capacity: number | null;
    occupancy: number | null;
    ratio?: number | null;
    avg_occupancy?: number | null; // 0–5
    avg_noise?: number | null;     // 0–5
    rating_count?: number | null;
    image_url?: string | null;
  };
};
type FeatureCollection = { type: "FeatureCollection"; features: Feature[] };

function colorFor(ratio: number) {
  if (ratio <= 0.25) return "#2ecc71";
  if (ratio <= 0.5) return "#bada55";
  if (ratio <= 0.75) return "#f1c40f";
  if (ratio <= 1.0) return "#e67e22";
  return "#e74c3c";
}
function fmt1(x: number | null | undefined) {
  if (x == null || Number.isNaN(x)) return "—";
  return (Math.round(x * 10) / 10).toFixed(1);
}

export default function MapViewWeb() {
  const mapRef = useRef<any>(null);
  const layerRef = useRef<any>(null);
  const [loaded, setLoaded] = useState(false);

  const fetchGeo = useCallback(async (): Promise<FeatureCollection | null> => {
    try {
      return await fetchJSON<FeatureCollection>(API.venuesGeoJSON);
    } catch {
      return null;
    }
  }, []);

  const renderFeatures = useCallback((fc: FeatureCollection | null) => {
    const map = mapRef.current;
    const group = layerRef.current;
    if (!map || !group) return;

    group.clearLayers();
    if (!fc) return;

    const L = (window as any).L;

    fc.features.forEach((f) => {
      const [lon, lat] = f.geometry.coordinates;
      const p = f.properties;

      const cap = p.capacity ?? 0;
      const occ = p.occupancy ?? 0;
      const ratio = typeof p.ratio === "number" ? p.ratio : (cap > 0 ? occ / cap : 0);
      const color = colorFor(ratio);

      const marker = L.circleMarker([lat, lon], {
        radius: Math.max(8, 30 * Math.min(1, ratio + 0.15)),
        color,
        fillColor: color,
        fillOpacity: 0.8,
        weight: 0,
      });

      const img = p.image_url
        ? `<img src="${p.image_url}" alt="${p.name}" style="width:100%;height:120px;object-fit:cover;border-radius:8px;margin:6px 0"/>`
        : "";

      const html = `
        <div style="min-width:230px">
          <div style="font-weight:800;margin-bottom:4px">${p.name}</div>
          ${img}
          <div style="margin-bottom:6px">
            Presence: ${occ}/${cap} (${Math.round(ratio * 100)}%)<br/>
            Avg crowd (0–5): <b>${fmt1(p.avg_occupancy)}</b><br/>
            Avg noise (0–5): <b>${fmt1(p.avg_noise)}</b>
          </div>
          <div style="display:flex;gap:8px">
            <button data-action="checkin" data-venue="${p.id}"
              style="padding:6px 10px;border-radius:8px;border:none;background:#111;color:#fff;cursor:pointer">
              Check in
            </button>
            <button data-action="checkout" data-venue="${p.id}"
              style="padding:6px 10px;border-radius:8px;border:1px solid #111;background:#fff;cursor:pointer">
              Check out
            </button>
          </div>
        </div>
      `;
      marker.bindPopup(html);
      group.addLayer(marker);
    });
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Inject Leaflet CSS
    const cssHref = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    let cssEl = document.querySelector<HTMLLinkElement>(`link[href="${cssHref}"]`);
    if (!cssEl) {
      cssEl = document.createElement("link");
      cssEl.rel = "stylesheet";
      cssEl.href = cssHref;
      document.head.appendChild(cssEl);
    }

    let cancelled = false;

    (async () => {
      const L = (await import("leaflet")).default;

      // Fix default marker icons from CDN
      // @ts-expect-error
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      if (cancelled) return;

      const map = L.map("map").setView([41.309, -72.927], 15);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(map);

      // Legend
      const legend = new (L.Control as any)({ position: "topright" as const });
      legend.onAdd = () => {
        const div = L.DomUtil.create("div", "legend");
        div.style.background = "white";
        div.style.padding = "8px 10px";
        div.style.borderRadius = "8px";
        div.style.boxShadow = "0 1px 3px rgba(0,0,0,0.25)";
        div.innerHTML = `
          <div style="font-weight:800;margin-bottom:4px">Legend</div>
          <div style="display:flex;gap:8px;align-items:center">
            <span style="display:inline-block;width:10px;height:10px;background:${colorFor(0.1)};border-radius:50%"></span> Empty
            <span style="display:inline-block;width:10px;height:10px;background:${colorFor(0.5)};border-radius:50%"></span> Moderate
            <span style="display:inline-block;width:10px;height:10px;background:${colorFor(0.9)};border-radius:50%"></span> Full
          </div>`;
        return div;
      };
      legend.addTo(map);

      const group = L.layerGroup().addTo(map);
      (window as any).L = (window as any).L || L;
      mapRef.current = map;
      layerRef.current = group;
      setLoaded(true);

      // Wire popup buttons (check-in/checkout) + refresh
      map.on("popupopen", (e: any) => {
        const rootEl = (e.popup?.getElement?.() ?? null) as HTMLElement | null;
        if (!rootEl) return;

        const handle = async (action: "checkin" | "checkout", vid: number) => {
          try {
            const { addAuthHeaders } = await import("@/constants/api");
            if (action === "checkin") {
              await fetch(API.checkins, {
                method: "POST",
                credentials: "include",
                headers: addAuthHeaders({ "Content-Type": "application/json" }),
                body: JSON.stringify({ venue_id: vid }),
              });
            } else {
              await fetch(API.checkout, {
                method: "POST",
                credentials: "include",
                headers: addAuthHeaders(),
              });
            }
          } finally {
            const fc = await fetchGeo();
            renderFeatures(fc);
          }
        };

        const buttons = rootEl.querySelectorAll('button[data-action]') as NodeListOf<HTMLButtonElement>;
        buttons.forEach((btn) => {
          const action = (btn.getAttribute("data-action") || "") as "checkin" | "checkout";
          const vid = Number(btn.getAttribute("data-venue"));
          btn.onclick = () => handle(action, vid);
        });
      });

      const drawOnce = async () => renderFeatures(await fetchGeo());
      await drawOnce();

      const pollId = window.setInterval(drawOnce, 15000);
      const beatId = window.setInterval(async () => {
        const { addAuthHeaders } = await import("@/constants/api");
        fetch(API.heartbeat, {
          method: "POST",
          credentials: "include",
          headers: addAuthHeaders(),
        }).catch(() => {});
      }, 60000);

      return () => {
        clearInterval(pollId);
        clearInterval(beatId);
        try { legend.remove(); } catch {}
        try { map.remove(); } catch {}
      };
    })();

    return () => { cancelled = true; };
  }, [fetchGeo, renderFeatures]);

  return (
    <div
      id="map"
      style={{
        width: "100%",
        height: "100%",
        minHeight: 400,
        opacity: loaded ? 1 : 0.6,
        transition: "opacity .2s ease",
      }}
    />
  );
}
