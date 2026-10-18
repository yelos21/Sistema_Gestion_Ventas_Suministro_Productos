import { useState } from "react";
import { api } from "./api";

interface Entrada {
  titulo: string;
  ok: boolean;
  datos: unknown;
}

interface Accion {
  texto: string;
  ir: () => void;
  peligro?: boolean;
}

export default function PracticaBD() {
  const [bd, setBd] = useState("practica_proyecto");
  const [nuevo, setNuevo] = useState("practica_renombrada");
  const [log, setLog] = useState<Entrada[]>([]);
  const [ocupado, setOcupado] = useState(false);

  async function ejecutar(titulo: string, ruta: string, metodo = "GET", cuerpo?: unknown) {
    setOcupado(true);
    try {
      const datos = await api<unknown>(ruta, {
        method: metodo,
        body: cuerpo ? JSON.stringify(cuerpo) : undefined,
      });
      setLog((l) => [{ titulo, ok: true, datos }, ...l]);
    } catch (e) {
      setLog((l) => [{ titulo, ok: false, datos: (e as Error).message }, ...l]);
    } finally {
      setOcupado(false);
    }
  }

  function confirmar(texto: string, titulo: string, ruta: string, metodo: string) {
    if (confirm(texto)) ejecutar(titulo, ruta, metodo);
  }

  const base = `/practica/${bd}`;

  const secciones: { id: string; titulo: string; acciones: Accion[] }[] = [
    {
      id: "4.1",
      titulo: "Bases de datos",
      acciones: [
        { texto: "Listar bases", ir: () => ejecutar("Listar bases", "/practica/bases") },
        { texto: "Crear base", ir: () => ejecutar(`Crear ${bd}`, "/practica/bases", "POST", { nombre: bd }) },
        {
          texto: "Renombrar",
          ir: () => ejecutar(`Renombrar ${bd} a ${nuevo}`, `/practica/bases/${bd}`, "PATCH", { nuevo }),
        },
        {
          texto: "Eliminar base",
          peligro: true,
          ir: () => confirmar(`¿Eliminar ${bd}?`, `Eliminar ${bd}`, `/practica/bases/${bd}`, "DELETE"),
        },
      ],
    },
    {
      id: "4.2",
      titulo: "Tablas y registros",
      acciones: [
        { texto: "Crear tablas", ir: () => ejecutar("Crear tablas", `${base}/tablas`, "POST") },
        { texto: "Ver tablas", ir: () => ejecutar("Ver tablas", `${base}/tablas`) },
        { texto: "ALTER TABLE", ir: () => ejecutar("ALTER TABLE", `${base}/alterar`, "POST") },
        { texto: "INSERT, SELECT, UPDATE, DELETE", ir: () => ejecutar("CRUD", `${base}/crud`, "POST") },
        {
          texto: "Borrar tablas",
          peligro: true,
          ir: () => confirmar(`¿Borrar todas las tablas de ${bd}?`, "Borrar tablas", `${base}/tablas`, "DELETE"),
        },
      ],
    },
    {
      id: "4.3",
      titulo: "Restricciones",
      acciones: [
        { texto: "Aplicar CHECK, DEFAULT e INDEX", ir: () => ejecutar("Aplicar restricciones", `${base}/restricciones`, "POST") },
        { texto: "Probar restricciones", ir: () => ejecutar("Probar restricciones", `${base}/restricciones/probar`, "POST") },
        { texto: "Ver restricciones", ir: () => ejecutar("Ver restricciones", `${base}/restricciones`) },
      ],
    },
    {
      id: "4.4",
      titulo: "Base del proyecto completa",
      acciones: [
        {
          texto: "Crear todo desde cero",
          peligro: true,
          ir: () =>
            confirmar(`Esto borra y vuelve a crear ${bd}. ¿Continuar?`, `Proyecto completo en ${bd}`, `${base}/proyecto-completo`, "POST"),
        },
      ],
    },
  ];

  const campo =
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200";

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-6 py-6">
      <div>
        <h1 className="text-xl font-bold">Práctica de base de datos</h1>
        <p className="text-sm text-slate-500">
          Solo trabaja con bases que empiezan con practica_. La base real del proyecto no se toca.
        </p>
      </div>

      <section className="grid gap-3 rounded-xl border bg-white p-5 shadow-sm sm:grid-cols-2">
        <label className="text-sm">
          Base de trabajo
          <input className={campo} value={bd} onChange={(e) => setBd(e.target.value)} />
        </label>
        <label className="text-sm">
          Nuevo nombre (para renombrar)
          <input className={campo} value={nuevo} onChange={(e) => setNuevo(e.target.value)} />
        </label>
      </section>

      {secciones.map((s) => (
        <section key={s.id} className="rounded-xl border bg-white p-5 shadow-sm">
          <h2 className="mb-3 font-semibold">
            {s.id} {s.titulo}
          </h2>
          <div className="flex flex-wrap gap-2">
            {s.acciones.map((a) => (
              <button
                key={a.texto}
                onClick={a.ir}
                disabled={ocupado}
                className={`rounded-lg px-3 py-2 text-sm font-medium text-white disabled:opacity-40 ${
                  a.peligro ? "bg-red-600 hover:bg-red-700" : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {a.texto}
              </button>
            ))}
          </div>
        </section>
      ))}

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
