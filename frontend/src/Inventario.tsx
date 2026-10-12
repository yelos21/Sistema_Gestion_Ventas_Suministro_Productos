import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

interface Categoria {
  id: number;
  nombre: string;
}

interface Producto {
  id: number;
  codigo: string;
  nombre: string;
  precio_compra: string | number;
  precio_venta: string | number;
  stock: number;
  stock_minimo: number;
  categoria_id: number;
}

const vacio = {
  codigo: "",
  nombre: "",
  precio_compra: "",
  precio_venta: "",
  stock: "0",
  stock_minimo: "0",
  categoria_id: "",
};

const dinero = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
});

export default function App() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [form, setForm] = useState(vacio);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState("");
  const [mostrarForm, setMostrarForm] = useState(false);

  function cargar() {
    api<Producto[]>("/productos")
      .then(setProductos)
      .catch((e: Error) => setError(e.message));
  }

  useEffect(() => {
    cargar();
    api<Categoria[]>("/categorias")
      .then(setCategorias)
      .catch((e: Error) => setError(e.message));
  }, []);

  const nombreCategoria = useMemo(
    () => Object.fromEntries(categorias.map((c) => [c.id, c.nombre])),
    [categorias]
  );

  const filtrados = productos.filter((p) =>
    (p.nombre + " " + p.codigo).toLowerCase().includes(busqueda.toLowerCase())
  );

  const bajos = productos.filter((p) => p.stock <= p.stock_minimo).length;
  const valorInventario = productos.reduce(
    (suma, p) => suma + Number(p.precio_venta) * p.stock,
    0
  );

  const resumen = [
    { titulo: "Productos", valor: String(productos.length) },
    { titulo: "Stock bajo", valor: String(bajos), alerta: bajos > 0 },
    { titulo: "Valor del inventario", valor: dinero.format(valorInventario) },
  ];

  function cambiar(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api<Producto>("/productos", {
        method: "POST",
        body: JSON.stringify({
          codigo: form.codigo,
          nombre: form.nombre,
          precio_compra: Number(form.precio_compra),
          precio_venta: Number(form.precio_venta),
          stock: Number(form.stock),
          stock_minimo: Number(form.stock_minimo),
          categoria_id: Number(form.categoria_id),
        }),
      });
      setForm(vacio);
      setMostrarForm(false);
      cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const campo =
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Encabezado */}
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-bold">Gestión de Ventas</h1>
            <p className="text-sm text-slate-500">Inventario de productos</p>
          </div>
          <button
            onClick={() => setMostrarForm(!mostrarForm)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {mostrarForm ? "Cerrar" : "+ Nuevo producto"}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-6 py-6">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Tarjetas de resumen */}
        <section className="grid gap-4 sm:grid-cols-3">
          {resumen.map((r) => (
            <div key={r.titulo} className="rounded-xl border bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">{r.titulo}</p>
              <p
                className={`mt-1 text-2xl font-bold ${
                  r.alerta ? "text-red-600" : ""
                }`}
              >
                {r.valor}
              </p>
            </div>
          ))}
        </section>

        {/* Formulario */}
        {mostrarForm && (
          <form
            onSubmit={guardar}
            className="grid gap-3 rounded-xl border bg-white p-5 shadow-sm sm:grid-cols-2"
          >
            <h2 className="font-semibold sm:col-span-2">Nuevo producto</h2>
            <input className={campo} name="codigo" placeholder="Código" value={form.codigo} onChange={cambiar} required />
            <input className={campo} name="nombre" placeholder="Nombre" value={form.nombre} onChange={cambiar} required />
            <input className={campo} name="precio_compra" type="number" step="0.01" placeholder="Precio compra" value={form.precio_compra} onChange={cambiar} required />
            <input className={campo} name="precio_venta" type="number" step="0.01" placeholder="Precio venta" value={form.precio_venta} onChange={cambiar} required />
            <input className={campo} name="stock" type="number" placeholder="Stock" value={form.stock} onChange={cambiar} />
            <input className={campo} name="stock_minimo" type="number" placeholder="Stock mínimo" value={form.stock_minimo} onChange={cambiar} />
            <select className={campo} name="categoria_id" value={form.categoria_id} onChange={cambiar} required>
              <option value="">Categoría...</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>
            <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              Guardar producto
            </button>
          </form>
        )}

        {/* Tabla */}
        <section className="overflow-hidden rounded-xl border bg-white shadow-sm">
          <div className="border-b p-4">
            <input
              className={campo}
              placeholder="Buscar por nombre o código..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
          </div>

          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Código</th>
                <th className="px-4 py-3 font-medium">Producto</th>
                <th className="px-4 py-3 font-medium">Categoría</th>
                <th className="px-4 py-3 text-right font-medium">Precio</th>
                <th className="px-4 py-3 text-center font-medium">Stock</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtrados.map((p) => {
                const bajo = p.stock <= p.stock_minimo;
                return (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-slate-500">{p.codigo}</td>
                    <td className="px-4 py-3 font-medium">{p.nombre}</td>
                    <td className="px-4 py-3">{nombreCategoria[p.categoria_id] ?? "-"}</td>
                    <td className="px-4 py-3 text-right">{dinero.format(Number(p.precio_venta))}</td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                          bajo
                            ? "bg-red-100 text-red-700"
                            : "bg-green-100 text-green-700"
                        }`}
                      >
                        {p.stock} {bajo && "· Bajo"}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {filtrados.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                    No hay productos que mostrar
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  );
}