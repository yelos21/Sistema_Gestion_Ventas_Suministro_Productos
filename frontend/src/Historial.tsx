import { useEffect, useState } from "react";
import { api } from "./api";

interface VentaResumen {
  id: number;
  fecha: string;
  metodo_pago: string;
  articulos: number;
  total: string | number;
}

const dinero = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });

export default function Historial() {
  const [ventas, setVentas] = useState<VentaResumen[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<VentaResumen[]>("/ventas/resumen")
      .then(setVentas)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <main className="mx-auto max-w-5xl px-6 py-6">
      <h1 className="mb-4 text-xl font-bold">Historial de ventas</h1>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <section className="overflow-hidden rounded-xl border bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Venta</th>
              <th className="px-4 py-3 font-medium">Fecha</th>
              <th className="px-4 py-3 font-medium">Pago</th>
              <th className="px-4 py-3 text-center font-medium">Artículos</th>
              <th className="px-4 py-3 text-right font-medium">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {ventas.map((v) => (
              <tr key={v.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 text-slate-500">#{v.id}</td>
                <td className="px-4 py-3">{new Date(v.fecha).toLocaleString("es-MX")}</td>
                <td className="px-4 py-3 capitalize">{v.metodo_pago}</td>
                <td className="px-4 py-3 text-center">{v.articulos}</td>
                <td className="px-4 py-3 text-right font-medium">
                  {dinero.format(Number(v.total))}
                </td>
              </tr>
            ))}
            {ventas.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  Aún no hay ventas
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}