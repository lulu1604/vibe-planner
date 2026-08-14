/* =====================================================================
   VibePlanner v2 - calendario.js
   MODULO C (Jose Cabrera) - navegacion e invitaciones.

   JavaScript vanilla, sin build ni CDN. Todo lo de aqui es MEJORA: si el
   script no carga, la navegacion entre meses sigue funcionando (son
   enlaces) y el link de invitacion se puede generar igual (es un <form>
   POST normal). Nada depende de que exista.
   ===================================================================== */
(function () {
  "use strict";

  /* -------------------------------------------------------------------
     1. Navegacion de meses con el teclado
     Flecha izquierda / derecha para cambiar de mes. Se salta cuando el
     foco esta dentro de un campo, o escribir "Reunion" en el titulo
     cambiaria de mes en cada vocal.
     ------------------------------------------------------------------- */
  var contenedor = document.querySelector("[data-calendario]");
  if (contenedor) {
    document.addEventListener("keydown", function (evento) {
      if (evento.altKey || evento.ctrlKey || evento.metaKey) return;

      var activo = document.activeElement;
      var escribiendo = activo && (
        activo.tagName === "INPUT" || activo.tagName === "TEXTAREA" ||
        activo.tagName === "SELECT" || activo.isContentEditable
      );
      if (escribiendo) return;

      var destino = null;
      if (evento.key === "ArrowLeft")  destino = contenedor.dataset.mesAnterior;
      if (evento.key === "ArrowRight") destino = contenedor.dataset.mesSiguiente;
      if (!destino) return;

      evento.preventDefault();
      window.location.href = destino;
    });
  }

  /* -------------------------------------------------------------------
     2. Generar el link de invitacion (US12)
     El formulario es un POST normal con su token CSRF; esto solo evita
     recargar la pagina para ensenar el link.
     ------------------------------------------------------------------- */
  var boton = document.getElementById("btn-invite");
  var form = document.getElementById("invite-form");
  var salida = document.getElementById("invite-result");

  if (boton && form && salida) {
    boton.addEventListener("click", function () {
      boton.disabled = true;
      var textoOriginal = boton.textContent;
      boton.textContent = "Generando...";

      fetch(form.action, { method: "POST", body: new FormData(form) })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (datos) {
          if (!datos || !datos.invite_url) {
            salida.textContent = "No se pudo generar el link. Vuelve a intentarlo.";
            return;
          }
          mostrarLink(datos.invite_url);
        })
        .catch(function () {
          salida.textContent = "No se pudo generar el link. Vuelve a intentarlo.";
        })
        .finally(function () {
          boton.disabled = false;
          boton.textContent = textoOriginal;
        });
    });
  }

  function mostrarLink(url) {
    // Se construye con createElement y .value, no con innerHTML: meter una
    // URL dentro de una plantilla de HTML es como se cuela una comilla y se
    // convierte en inyeccion. Aqui la URL es nuestra, pero el habito es lo
    // que evita el dia que no lo sea.
    salida.textContent = "";

    var etiqueta = document.createElement("label");
    etiqueta.className = "field-etiqueta";
    etiqueta.setAttribute("for", "invite-url");
    etiqueta.textContent = "Link de invitacion";

    var campo = document.createElement("input");
    campo.className = "field-control";
    campo.id = "invite-url";
    campo.type = "text";
    campo.readOnly = true;
    campo.value = url;
    campo.addEventListener("focus", function () { campo.select(); });

    var ayuda = document.createElement("span");
    ayuda.className = "field-ayuda";
    ayuda.textContent = "Copialo y compartelo por donde quieras. Quien lo abra "
                      + "tendra que iniciar sesion para aceptar.";

    var contenedorCampo = document.createElement("div");
    contenedorCampo.className = "field";
    contenedorCampo.append(etiqueta, campo, ayuda);

    salida.appendChild(contenedorCampo);
    salida.classList.remove("hidden");
    campo.focus();
  }
})();
