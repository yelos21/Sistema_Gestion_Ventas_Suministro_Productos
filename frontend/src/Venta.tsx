import { useEffect, useState } from "react";
import { api } from "./api";

interface Producto {
  id: number;
  codigo: string;
  nombre: string;
  precio_venta: string | number;
  stock: number;
}

interface RespuestaVenta {
  venta_id: number;
  total: string | number;
  mensaje: string;
}

const dinero = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
});

export default function Venta() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [carrito, setCarrito] = useState<Record<number, number>>({});
  const [busqueda, setBusqueda] = useState("");
  const [metodo, setMetodo] = useState("efectivo");
  const [error, setError] = useState<string | null>(null);
  const [exito, setExito] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function cargar() {
    api<Producto[]>("/productos")
      .then(setProductos)
      .catch((e: Error) => setError(e.message));
  }

  useEffect(() => {
    cargar();
  }, []);

  function agregar(p: Producto) {
    setExito(null);
    setCarrito((c) => {
      const actual = c[p.id] ?? 0;
      if (actual >= p.stock) return c;
      return { ...c, [p.id]: actual + 1 };
    });
  }

  function cambiarCantidad(p: Producto, delta: number) {
    setCarrito((c) => {
      const nueva = (c[p.id] ?? 0) + delta;
      if (nueva > p.stock) return c;
      const copia = { ...c };
      if (nueva <= 0) {
        delete copia[p.id];
      } else {
        copia[p.id] = nueva;
      }
      return copia;
    });
  }

  const lineas = productos
    .filter((p) => carrito[p.id])
    .map((p) => ({ p, cantidad: carrito[p.id] }));

  const total = lineas.reduce(
    (suma, l) => suma + Number(l.p.precio_venta) * l.cantidad,
    0
  );

  const filtrados = productos.filter((p) =>
    (p.nombre + " " + p.codigo).toLowerCase().includes(busqueda.toLowerCase())
  );

  async function cobrar() {
    setError(null);
    setExito(null);
    setEnviando(true);
    try {
      const r = await api<RespuestaVenta>("/ventas", {
        method: "POST",
        body: JSON.stringify({
          cliente_id: null,
          metodo_pago: metodo,
          items: lineas.map((l) => ({
            producto_id: l.p.id,
            cantidad: l.cantidad,
          })),
        }),
      });
      setExito(
        `Venta #${r.venta_id} registrada por ${dinero.format(Number(r.total))}`
      );
      setCarrito({});
      cargar();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-6">
      <h1 className="mb-4 text-xl font-bold">Nueva venta</h1>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {exito && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {exito}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Productos */}
        <section className="rounded-xl border bg-white shadow-sm lg:col-span-2">
          <div className="border-b p-4">
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              placeholder="Buscar por nombre o código..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </div>
          <ul className="divide-y">
            {filtrados.map((p) => (
              <li key={p.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="font-medium">{p.nombre}</p>
                  <p className="text-sm text-slate-500">
                    {dinero.format(Number(p.precio_venta))} · Stock: {p.stock}
                  </p>
                </div>
                <button
                  onClick={() => agregar(p)}
                  disabled={p.stock === 0}
                  className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-40"
                >
                  Agregar
                </button>
              </li>
            ))}
            {filtrados.length === 0 && (
              <li className="px-4 py-8 text-center text-slate-400">
                No hay productos que mostrar
              </li>
            )}
          </ul>
        </section>

        {/* Carrito */}
        <aside className="h-fit rounded-xl border bg-white p-5 shadow-sm">
          <h2 className="mb-3 font-semibold">Carrito</h2>

          {lineas.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-400">
              Aún no hay productos
            </p>
          ) : (
            <ul className="space-y-3">
              {lineas.map(({ p, cantidad }) => (
                <li key={p.id} className="flex items-center justify-between gap-2 text-sm">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{p.nombre}</p>
                    <p className="text-slate-500">
                      {dinero.format(Number(p.precio_venta) * cantidad)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => cambiarCantidad(p, -1)}
                      className="h-7 w-7 rounded border hover:bg-slate-100"
                    >
                      −
                    </button>
                    <span className="w-5 text-center">{cantidad}</span>
                    <button
                      onClick={() => cambiarCantidad(p, 1)}
                      className="h-7 w-7 rounded border hover:bg-slate-100"
                    >
                      +
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <div className="mt-4 space-y-3 border-t pt-4">
            <select
              value={metodo}
              onChange={(e) => setMetodo(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="efectivo">Efectivo</option>
              <option value="tarjeta">Tarjeta</option>
              <option value="transferencia">Transferencia</option>
            </select>

            <div className="flex items-center justify-between text-lg font-bold">
              <span>Total</span>
              <span>{dinero.format(total)}</span>
            </div>

            <button
              onClick={cobrar}
              disabled={lineas.length === 0 || enviando}
              className="w-full rounded-lg bg-green-600 py-2.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-40"
            >
              {enviando ? "Registrando..." : "Cobrar"}
            </button>
          </div>
        </aside>
      </div>
    </main>
  );
}