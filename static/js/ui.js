/* =====================================================================
   VibePlanner v2 - ui.js
   JavaScript vanilla. Sin build, sin dependencias, sin CDN.

   Todo lo de aqui es MEJORA, no requisito: si el JavaScript no carga, los
   formularios se envian igual, los modales se abren igual (son <dialog> y
   <form method="dialog">) y la aplicacion sigue siendo usable.
   ===================================================================== */
(function () {
  "use strict";

  /* -------------------------------------------------------------------
     1. Evitar el doble envio
     H1: el boton dice que esta pasando en vez de quedarse mudo mientras
     el servidor responde, y de paso no se crean dos cuentas por un
     doble clic impaciente.
     ------------------------------------------------------------------- */
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      var boton = form.querySelector("[data-enviando]");
      if (!boton || boton.dataset.yaEnviado) return;
      boton.dataset.yaEnviado = "1";
      boton.textContent = boton.dataset.enviando;
      // disabled cancelaria el envio del propio boton: se desactiva despues.
      setTimeout(function () { boton.disabled = true; }, 0);
    });
  });

  /* -------------------------------------------------------------------
     2. Modales
     Se usa <dialog> nativo, que ya trae el cierre con Escape, la trampa
     de foco y la devolucion del foco al boton que lo abrio. Aqui solo
     falta la tercera forma de cerrar: el clic fuera.
     ------------------------------------------------------------------- */
  document.querySelectorAll("[data-abre-modal]").forEach(function (disparador) {
    disparador.addEventListener("click", function () {
      var modal = document.getElementById(disparador.dataset.abreModal);
      if (modal && typeof modal.showModal === "function") modal.showModal();
    });
  });

  // Cierre 1 de 3: los botones "x" y "Cancelar".
  document.querySelectorAll("[data-cierra-modal]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      var modal = boton.closest("dialog");
      if (modal) modal.close();
    });
  });

  // Cierre 2 de 3: clic fuera. (El 3 es Escape, y lo trae <dialog> de fabrica,
  // igual que devolver el foco al boton que lo abrio.)
  document.querySelectorAll("dialog.modal").forEach(function (modal) {
    modal.addEventListener("click", function (evento) {
      // El <dialog> ocupa toda la pantalla; el recuadro visible es su caja.
      // Si el clic cae fuera de esa caja, fue en el fondo.
      if (evento.target !== modal) return;
      var caja = modal.getBoundingClientRect();
      var fuera = evento.clientX < caja.left || evento.clientX > caja.right ||
                  evento.clientY < caja.top  || evento.clientY > caja.bottom;
      if (fuera) modal.close();
    });
  });

  // Un formulario que volvio con errores de validacion reabre su modal solo:
  // si no, los mensajes de error quedarian dentro de un dialogo cerrado y la
  // pantalla pareceria no haber hecho nada.
  var modalPendiente = document.querySelector("dialog[data-abrir-al-cargar]");
  if (modalPendiente && typeof modalPendiente.showModal === "function") {
    modalPendiente.showModal();
    var primerError = modalPendiente.querySelector("[aria-invalid='true']");
    if (primerError) primerError.focus();
  }

  /* -------------------------------------------------------------------
     3. Aviso de campo ya tomado (solo en el panel de administracion)
     La comprobacion al salir del campo evita rellenar todo el formulario
     para descubrir al enviarlo que el usuario ya existia.

     NO existe en el registro publico a proposito: ahi seria un
     comprobador de cuentas validas con URL abierta. Aqui el endpoint
     exige el permiso `usuario.crear`.
     ------------------------------------------------------------------- */
  var campoUsuario = document.querySelector("[data-comprueba-disponible]");
  if (campoUsuario) {
    campoUsuario.addEventListener("blur", function () {
      var valor = campoUsuario.value.trim().toLowerCase();
      if (valor.length < 3) return;

      fetch(campoUsuario.dataset.compruebaDisponible + "?username=" + encodeURIComponent(valor))
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (datos) {
          if (!datos) return;
          var aviso = document.getElementById("aviso-disponible");
          if (!aviso) return;
          aviso.textContent = datos.disponible ? "" : "Ese nombre de usuario ya esta en uso.";
          campoUsuario.setAttribute("aria-invalid", datos.disponible ? "false" : "true");
        })
        .catch(function () { /* sin red: el servidor lo valida igual al enviar */ });
    });
  }
})();
