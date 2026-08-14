// VibePlanner - kanban.js
// DUENA: Lucero Ayala (Módulo B)
//
// Drag & drop del tablero Kanban (US9).
//
// Política de optimismo seguro:
//   1. Se pinta el movimiento en el DOM inmediatamente (optimista).
//   2. Se envía POST al servidor con fetch.
//   3. Si el servidor responde error → la tarjeta VUELVE a su columna original.
//   Una interfaz que muestra un cambio que no se guardó es peor que una lenta.
//
// El CSRF_TOKEN se define en kanban.html antes de cargar este script.
// La columna se valida TAMBIÉN en el servidor (planner.py) → HTTP 400 si es inválida.

document.addEventListener("DOMContentLoaded", () => {
  const board = document.getElementById("kanban-board");
  if (!board) return;

  // ── Estado del drag ──────────────────────────────────────────────
  let cardDraggeada = null;
  let colOrigenId = null;  // id del contenedor de tarjetas original

  // ── Eventos de las tarjetas ──────────────────────────────────────
  function activarDrag(card) {
    card.addEventListener("dragstart", (e) => {
      cardDraggeada = card;
      colOrigenId = card.parentElement.id; // "cards-backlog", etc.
      card.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
    });

    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
      document.querySelectorAll(".kanban-col").forEach((col) =>
        col.classList.remove("drop-over")
      );
      cardDraggeada = null;
      colOrigenId = null;
    });
  }

  document.querySelectorAll(".kanban-card").forEach(activarDrag);

  // ── Eventos de las columnas ──────────────────────────────────────
  document.querySelectorAll(".kanban-col").forEach((col) => {
    col.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      col.classList.add("drop-over");
    });

    col.addEventListener("dragleave", (e) => {
      // Solo quitar si salimos del col, no de un hijo
      if (!col.contains(e.relatedTarget)) {
        col.classList.remove("drop-over");
      }
    });

    col.addEventListener("drop", async (e) => {
      e.preventDefault();
      col.classList.remove("drop-over");
      if (!cardDraggeada) return;

      const destColumn = col.dataset.column;
      const origenColumn = cardDraggeada.dataset.currentCol;
      if (destColumn === origenColumn) return; // Sin cambio

      const taskId = cardDraggeada.dataset.taskId;
      const contenedorOrigen = document.getElementById(colOrigenId);
      const contenedorDestino = col.querySelector(".kanban-cards");

      // 1. Mover optimistamente en el DOM
      contenedorDestino.appendChild(cardDraggeada);
      cardDraggeada.dataset.currentCol = destColumn;
      _actualizarContadores();

      // 2. Persistir en el servidor
      try {
        const res = await fetch(`/tasks/${taskId}/column`, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-Token": typeof CSRF_TOKEN !== "undefined" ? CSRF_TOKEN : "",
          },
          body: `column=${encodeURIComponent(destColumn)}&_csrf=${encodeURIComponent(
            typeof CSRF_TOKEN !== "undefined" ? CSRF_TOKEN : ""
          )}`,
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
      } catch (err) {
        // 3. Revertir si el servidor responde error
        console.warn("Kanban: error al mover, revirtiendo.", err);
        contenedorOrigen.appendChild(cardDraggeada);
        cardDraggeada.dataset.currentCol = origenColumn;
        _actualizarContadores();
        _mostrarToast("No se pudo mover la tarjeta. Inténtalo de nuevo.");
      }
    });
  });

  // ── Helpers ────────────────────────────────────────────────────
  function _actualizarContadores() {
    document.querySelectorAll(".kanban-col").forEach((col) => {
      const contador = col.querySelector(".kanban-contador");
      const cards = col.querySelectorAll(".kanban-card");
      if (contador) contador.textContent = cards.length;
    });
  }

  function _mostrarToast(msg) {
    // Toast minimo: no necesitamos una librería
    const t = document.createElement("div");
    t.textContent = msg;
    Object.assign(t.style, {
      position: "fixed",
      bottom: "var(--space-6, 1.5rem)",
      left: "50%",
      transform: "translateX(-50%)",
      background: "var(--navy, #2F4156)",
      color: "var(--beige, #F5EFEB)",
      padding: "var(--space-3, .75rem) var(--space-6, 1.5rem)",
      borderRadius: "var(--radius-pill, 999px)",
      zIndex: "9999",
      fontSize: "var(--text-sm, .875rem)",
      boxShadow: "var(--shadow-lg)",
    });
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3500);
  }
});
