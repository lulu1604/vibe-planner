// VibePlanner - logica frontend. DUENA: Piero
// US4: pide el desglose a la API y lo muestra en el modal.

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("score-modal");
  const totalEl = document.getElementById("modal-total");
  const listEl = document.getElementById("modal-breakdown");

  document.querySelectorAll(".why-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.taskId;
      const available =
        document.querySelector('input[name="available"]')?.value || 120;

      const res = await fetch(
        `/api/task/${id}/score-breakdown?available=${available}`
      );
      const data = await res.json();

      totalEl.textContent = `Puntaje total: ${data.total} pts`;
      listEl.innerHTML = "";
      for (const [clave, valor] of Object.entries(data.breakdown)) {
        const li = document.createElement("li");
        li.textContent = `${clave}: +${valor.puntos} - ${valor.razon}`;
        listEl.appendChild(li);
      }
      modal.hidden = false;
    });
  });

  document.getElementById("modal-close")?.addEventListener("click", () => {
    modal.hidden = true;
  });
});
