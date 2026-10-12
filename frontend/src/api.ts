const BASE = import.meta.env.VITE_API_URL as string;

export async function api<T>(ruta: string, opciones?: RequestInit): Promise<T> {
  const r = await fetch(BASE + ruta, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  if (!r.ok) {
    let detalle = "Error " + r.status;
    try {
      detalle = (await r.json()).detail ?? detalle;
    } catch {}
    throw new Error(detalle);
  }
  if (r.status === 204) return undefined as T;
  return r.json() as Promise<T>;
}