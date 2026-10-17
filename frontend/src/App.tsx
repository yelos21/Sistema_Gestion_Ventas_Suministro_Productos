import { useState } from "react";
import Inventario from "./Inventario";
import Venta from "./Venta";
import Historial from "./Historial";

type Vista = "inventario" | "venta" | "historial";

const pestanas: { id: Vista; texto: string }[] = [
  { id: "inventario", texto: "Inventario" },
  { id: "venta", texto: "Nueva venta" },
  { id: "historial", texto: "Historial" },
];


export default function App() {
  const [vista, setVista] = useState<Vista>("inventario");

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <nav className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl gap-6 px-6">
          {pestanas.map((p) => (
            <button
              key={p.id}
              onClick={() => setVista(p.id)}
              className={`border-b-2 py-3 text-sm font-medium ${
                vista === p.id
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              {p.texto}
            </button>
          ))}
        </div>
      </nav>

      {vista === "inventario" ? <Inventario /> : vista === "venta" ? <Venta /> : <Historial />}
    </div>
  );
}