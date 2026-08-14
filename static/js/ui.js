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
     3. Menu de cuenta de la barra superior
     Patron "disclosure": un boton con aria-expanded que ensena u oculta
     un panel. Se cierra de tres formas -- volver a pulsar, Escape y clic
     fuera -- y Escape DEVUELVE EL FOCO al boton, que es lo que siempre
     se olvida y lo que deja a quien navega con teclado perdido en el
     principio del documento.
     ------------------------------------------------------------------- */
  var disparador = document.getElementById("menu-cuenta-boton");
  var panel = document.getElementById("menu-cuenta-panel");

  if (disparador && panel) {
    var abrirMenu = function (abierto) {
      disparador.setAttribute("aria-expanded", abierto ? "true" : "false");
      panel.hidden = !abierto;
    };

    disparador.addEventListener("click", function (evento) {
      evento.stopPropagation();
      abrirMenu(disparador.getAttribute("aria-expanded") !== "true");
    });

    // Los clics DENTRO del panel no cuentan como "fuera": sin esto, pulsar
    // un enlace del menu lo cerraria antes de que el navegador lo siguiera.
    panel.addEventListener("click", function (evento) {
      evento.stopPropagation();
    });

    document.addEventListener("click", function () {
      abrirMenu(false);
    });

    document.addEventListener("keydown", function (evento) {
      if (evento.key !== "Escape") return;
      if (disparador.getAttribute("aria-expanded") !== "true") return;
      abrirMenu(false);
      disparador.focus();
    });

    // Salir del menu con Tab tambien lo cierra: dejarlo abierto detras
    // mientras el foco esta en otra parte de la pagina desorienta.
    panel.addEventListener("focusout", function (evento) {
      if (!panel.contains(evento.relatedTarget) && evento.relatedTarget !== disparador) {
        abrirMenu(false);
      }
    });
  }

  /* -------------------------------------------------------------------
     4. Aviso de campo ya tomado (solo en el panel de administracion)
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
  /* -------------------------------------------------------------------
     Apariencia: tema de color
     El <head> ya aplico el tema guardado antes de pintar; esto solo maneja
     el cambio en vivo desde el panel.
     ------------------------------------------------------------------- */
  var CLAVE_TEMA = "vibeplanner-tema";
  var TEMAS = ["claro", "oscuro", "alto-contraste"];

  function aplicarTema(tema) {
    // Lista blanca. Lo que llega de localStorage acaba en un atributo del
    // <html>, y eso lo puede haber escrito cualquier script de la pagina.
    if (TEMAS.indexOf(tema) === -1) tema = "claro";

    if (tema === "claro") {
      document.documentElement.removeAttribute("data-tema");
    } else {
      document.documentElement.setAttribute("data-tema", tema);
    }
    try { localStorage.setItem(CLAVE_TEMA, tema); } catch (e) { /* sin almacenamiento */ }
  }

  function temaActual() {
    return document.documentElement.getAttribute("data-tema") || "claro";
  }

  var selector = document.querySelector("[data-selector-tema]");
  if (selector) {
    // Marcar el que esta puesto: si el panel abriera siempre en "Claro",
    // diria una cosa distinta de lo que se ve en la pantalla.
    var actual = selector.querySelector('input[value="' + temaActual() + '"]');
    if (actual) actual.checked = true;

    selector.addEventListener("change", function (evento) {
      if (evento.target.name === "tema") aplicarTema(evento.target.value);
    });
  }

  var botonRestablecer = document.querySelector("[data-restablece-tema]");
  if (botonRestablecer) {
    botonRestablecer.addEventListener("click", function () {
      aplicarTema("claro");
      var claro = document.querySelector('[data-selector-tema] input[value="claro"]');
      if (claro) claro.checked = true;
    });
  }
})();
