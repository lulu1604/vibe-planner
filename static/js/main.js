// VibePlanner - US4: explicabilidad del puntaje.
// DUENO: Piero Calderon
//
// Pide el desglose a la API y lo pinta como barras proporcionales, una por
// componente, con el color que le asigna el design system. Ver "por que 90
// puntos" en tres barras se entiende de un vistazo; leerlo en tres lineas de
// texto, no.
//
// Actualizado a la v2: el modal es un <dialog>, asi que el cierre con Escape,
// la trampa de foco y la devolucion del foco al boton que lo abrio salen
// gratis. Antes era un <div hidden> y nada de eso funcionaba con teclado.

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("score-modal");
  const totalEl = document.getElementById("modal-total");
  const listEl = document.getElementById("modal-breakdown");

  if (!modal || !totalEl || !listEl) return;

  // Maximo de cada componente segun scoring.py. Sirve para que el ancho de la
  // barra sea proporcional a lo que ese componente PODIA aportar, no al total.
  const MAXIMOS = { prioridad: 50, urgencia: 40, tiempo: 15 };
  const COLORES = {
    prioridad: "var(--score-priority)",
    urgencia: "var(--score-urgency)",
    tiempo: "var(--score-timefit)",
  };
  const ETIQUETAS = {
    prioridad: "Prioridad",
    urgencia: "Urgencia",
    tiempo: "Ajuste de tiempo",
  };

  document.querySelectorAll(".why-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.taskId;
      const available =
        document.querySelector('input[name="available"]')?.value || 120;

      let data;
      try {
        let res = await fetch(
          `/v2/api/task/${id}/score-breakdown?available=${available}`
        );
        if (!res.ok) {
          res = await fetch(
            `/api/task/${id}/score-breakdown?available=${available}`
          );
        }
        if (!res.ok) throw new Error(res.status);
        data = await res.json();
      } catch (e) {
        totalEl.textContent = "No pudimos calcular el desglose";
        listEl.innerHTML =
          "<li class='text-muted'>Recarga la página e inténtalo otra vez.</li>";
        modal.showModal();
        return;
      }

      totalEl.textContent = `${data.total} pts`;
      listEl.innerHTML = "";

      for (const [clave, valor] of Object.entries(data.breakdown)) {
        const maximo = MAXIMOS[clave] || 50;
        const ancho = Math.max(2, Math.round((valor.puntos / maximo) * 100));

        const li = document.createElement("li");

        const fila = document.createElement("div");
        fila.className = "fila-entre";

        const razon = document.createElement("span");
        razon.textContent = `${ETIQUETAS[clave] || clave} · ${valor.razon}`;

        const puntos = document.createElement("span");
        puntos.className = "text-data";
        puntos.style.fontWeight = "700";
        puntos.textContent = `+${valor.puntos}`;

        fila.append(razon, puntos);

        const carril = document.createElement("div");
        carril.className = "barra-progreso";
        carril.style.marginTop = "var(--space-1)";

        const relleno = document.createElement("div");
        relleno.className = "barra-progreso-relleno";
        relleno.style.width = `${ancho}%`;
        relleno.style.background = COLORES[clave] || "var(--teal-700)";
        carril.appendChild(relleno);

        li.append(fila, carril);
        listEl.appendChild(li);
      }

      modal.showModal();
    });
  });

  document.querySelectorAll("#modal-close, [data-cierra-modal]").forEach((el) => {
    el.addEventListener("click", () => {
      modal.close();
    });
  });
});
