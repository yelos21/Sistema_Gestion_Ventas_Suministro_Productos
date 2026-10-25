import { useState } from "react";
import { api } from "./api";

const BASE = import.meta.env.VITE_API_URL as string;
const RUTA = "/practica-admin";

interface Entrada {
  titulo: string;
  ok: boolean;
  datos: unknown;
}

// Descarga un archivo que genera el backend
async function bajar(ruta: string, nombre: string) {
  const r = await fetch(BASE + ruta);
  if (!r.ok) {
    let detalle = "Error " + r.status;
    try {
      detalle = (await r.json()).detail ?? detalle;
    } catch {}
    throw new Error(detalle);
  }
  const url = URL.createObjectURL(await r.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  a.click();
  URL.revokeObjectURL(url);
}

const boton = "rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-40";
const verde = `${boton} bg-green-600 hover:bg-green-700`;
const azul = `${boton} bg-blue-600 hover:bg-blue-700`;
const naranja = `${boton} bg-orange-600 hover:bg-orange-700`;
const gris = `${boton} bg-slate-600 hover:bg-slate-700`;
const archivoCss =
  "text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium hover:file:bg-slate-200";
const campo =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200";

export default function PracticaAdmin() {
  const [bd, setBd] = useState("practica_proyecto");
  const [destino, setDestino] = useState("practica_restaurada");
  const [tabla, setTabla] = useState("producto");
  const [archivoRespaldo, setArchivoRespaldo] = useState<File | null>(null);
  const [archivoDatos, setArchivoDatos] = useState<File | null>(null);
  const [log, setLog] = useState<Entrada[]>([]);
  const [ocupado, setOcupado] = useState(false);

  async function correr(titulo: string, accion: () => Promise<unknown>) {
    setOcupado(true);
    try {
      const datos = await accion();
      setLog((l) => [{ titulo, ok: true, datos }, ...l]);
    } catch (e) {
      setLog((l) => [{ titulo, ok: false, datos: (e as Error).message }, ...l]);
    } finally {
      setOcupado(false);
    }
  }

  const t = encodeURIComponent(tabla);

  function descargarRespaldo() {
    correr("Descargar respaldo", async () => {
      const nombre = `${bd}_respaldo.json`;
      await bajar(`${RUTA}/respaldo/${bd}`, nombre);
      return `Descargado ${nombre}`;
    });
  }

  function restaurar() {
    correr("Restaurar respaldo", async () => {
      if (!archivoRespaldo) throw new Error("Elige primero un archivo de respaldo (.json)");
      let respaldo: unknown;
      try {
        respaldo = JSON.parse(await archivoRespaldo.text());
      } catch {
        throw new Error("El archivo no es un JSON válido");
      }
      return api(`${RUTA}/restauracion`, {
        method: "POST",
        body: JSON.stringify({ destino, respaldo }),
      });
    });
  }

  function importar() {
    correr(`Importar a ${tabla}`, async () => {
      if (!archivoDatos) throw new Error("Elige primero un archivo .csv o .json");
      const nombre = archivoDatos.name.toLowerCase();
      const formato = nombre.endsWith(".csv") ? "csv" : nombre.endsWith(".json") ? "json" : null;
      if (!formato) throw new Error("El archivo debe ser .csv o .json");
      return api(`${RUTA}/migracion/${bd}/tabla/${t}/importar`, {
        method: "POST",
        body: JSON.stringify({ formato, contenido: await archivoDatos.text() }),
      });
    });
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-6 py-6">
      <div>
        <h1 className="text-xl font-bold">Práctica de administración</h1>
        <p className="text-sm text-slate-500">
          Trabaja solo con bases que empiezan con practica_. La base real del proyecto no se toca.
        </p>
      </div>

      <section className="grid gap-3 rounded-xl border bg-white p-5 shadow-sm sm:grid-cols-2">
        <label className="text-sm">
          Base de trabajo
          <input className={campo} value={bd} onChange={(e) => setBd(e.target.value)} />
        </label>
        <label className="text-sm">
          Base nueva donde se restaura
          <input className={campo} value={destino} onChange={(e) => setDestino(e.target.value)} />
        </label>
      </section>

      <section className="space-y-3 rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="font-semibold">4.4 Respaldo y restauración</h2>
        <div className="flex flex-wrap items-center gap-3">
          <button className={verde} disabled={ocupado} onClick={descargarRespaldo}>
            Descargar respaldo
          </button>
          <input
            type="file"
            accept=".json"
            className={archivoCss}
            onChange={(e) => setArchivoRespaldo(e.target.files?.[0] ?? null)}
          />
          <button className={naranja} disabled={ocupado} onClick={restaurar}>
            Restaurar
          </button>
        </div>
      </section>

      <section className="space-y-3 rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="font-semibold">4.5 Usuarios (10 usuarios con permisos)</h2>
        <div className="flex flex-wrap gap-3">
          <button
            className={verde}
            disabled={ocupado}
            onClick={() => correr("Crear 10 usuarios", () => api(`${RUTA}/usuarios/${bd}`, { method: "POST" }))}
          >
            Crear 10 usuarios
          </button>
          <button
            className={gris}
            disabled={ocupado}
            onClick={() =>
              correr("Script SQL de usuarios", async () => (await api<{ script: string }>(`${RUTA}/usuarios/script`)).script)
            }
          >
            Ver script SQL
          </button>
          <button
            className={gris}
            disabled={ocupado}
            onClick={() => correr("Permisos por usuario", () => api(`${RUTA}/usuarios/${bd}/permisos`))}
          >
            Ver permisos
          </button>
        </div>
      </section>

      <section className="space-y-3 rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="font-semibold">4.6 Importar y exportar</h2>
        <label className="block text-sm">
          Tabla (para CSV, JSON e importar)
          <input className={campo} value={tabla} onChange={(e) => setTabla(e.target.value)} />
        </label>
        <div className="flex flex-wrap gap-3">
          <button
            className={azul}
            disabled={ocupado}
            onClick={() => correr("Exportar a MySQL", async () => {
              await bajar(`${RUTA}/migracion/${bd}/mysql`, `${bd}_mysql.sql`);
              return `Descargado ${bd}_mysql.sql (ejecútalo con: mysql -u root -p < ${bd}_mysql.sql)`;
            })}
          >
            Exportar a MySQL
          </button>
          <button
            className={azul}
            disabled={ocupado}
            onClick={() => correr("Exportar a SQLite", async () => {
              await bajar(`${RUTA}/migracion/${bd}/sqlite`, `${bd}.sqlite`);
              return `Descargado ${bd}.sqlite`;
            })}
          >
            Exportar a SQLite
          </button>
          <button
            className={gris}
            disabled={ocupado}
            onClick={() => correr("Tabla a CSV", async () => {
              await bajar(`${RUTA}/migracion/${bd}/tabla/${t}/csv`, `${tabla}.csv`);
              return `Descargado ${tabla}.csv`;
            })}
          >
            Tabla a CSV
          </button>
          <button
            className={gris}
            disabled={ocupado}
            onClick={() => correr("Tabla a JSON", async () => {
              await bajar(`${RUTA}/migracion/${bd}/tabla/${t}/json`, `${tabla}.json`);
              return `Descargado ${tabla}.json`;
            })}
          >
            Tabla a JSON
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="file"
            accept=".csv,.json"
            className={archivoCss}
            onChange={(e) => setArchivoDatos(e.target.files?.[0] ?? null)}
          />
          <button className={naranja} disabled={ocupado} onClick={importar}>
            Importar a la tabla
          </button>
        </div>
      </section>

      <section className="rounded-xl border bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Resultado</h2>
          <button onClick={() => setLog([])} className="text-sm text-slate-500 hover:text-slate-800">
            Limpiar
          </button>
        </div>
        {log.length === 0 && <p className="text-sm text-slate-400">Pulsa un botón para ejecutar una acción</p>}
        <div className="space-y-3">
          {log.map((e, i) => (
            <div
              key={i}
              className={`rounded-lg border p-3 text-sm ${
                e.ok ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"
              }`}
            >
              <p className={`font-medium ${e.ok ? "text-green-700" : "text-red-700"}`}>
                {e.ok ? "OK" : "Error"}: {e.titulo}
              </p>
              <pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-xs text-slate-700">
                {typeof e.datos === "string" ? e.datos : JSON.stringify(e.datos, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
