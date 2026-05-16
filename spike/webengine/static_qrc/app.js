/* Pont QWebChannel minimal — spike PLO-44 (mode qrc:). */

(function () {
  const statusEl = document.getElementById("status");
  const cssEl = document.getElementById("css-check");
  const logEl = document.getElementById("log");
  const btn = document.getElementById("btn-ping");

  function log(line) {
    logEl.textContent += line + "\n";
  }

  /** Qt 6 WebChannel renvoie souvent une Promise pour les @Slot avec result. */
  function qtInvoke(callable) {
    const value = callable();
    if (value && typeof value.then === "function") {
      return value;
    }
    return Promise.resolve(value);
  }

  const cssOk = getComputedStyle(document.body).backgroundColor !== "rgba(0, 0, 0, 0)";
  cssEl.textContent = cssOk
    ? "CSS embarqué : chargé (fond teinté)"
    : "CSS embarqué : non détecté";
  cssEl.classList.toggle("ok", cssOk);

  if (typeof qt === "undefined") {
    statusEl.textContent = "Qt WebChannel indisponible (qt manquant).";
    return;
  }

  new QWebChannel(qt.webChannelTransport, function (channel) {
    const bridge = channel.objects.bridge;
    if (!bridge) {
      statusEl.textContent = "Objet « bridge » absent du QWebChannel.";
      return;
    }

    if (bridge.logFromJs && bridge.logFromJs.connect) {
      bridge.logFromJs.connect(function (msg) {
        log("← JS émis : " + msg);
      });
    }

    qtInvoke(function () {
      return bridge.loaderLabel ? bridge.loaderLabel() : "?";
    }).then(function (label) {
      statusEl.textContent = "Pont actif — mode " + label;
    });

    btn.addEventListener("click", function () {
      qtInvoke(function () {
        return bridge.ping("bonjour depuis le spike");
      }).then(function (reply) {
        log("→ ping : " + reply);
      });
    });

    qtInvoke(function () {
      return bridge.ping("démarrage");
    }).then(function (reply) {
      log("→ ping auto : " + reply);
    });
  });
})();
