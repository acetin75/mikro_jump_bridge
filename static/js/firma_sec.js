// firma_sec.html — bağlantı modu + AJAX testi
(function () {
  const cfgEl = document.getElementById("firma-sec-cfg");
  if (!cfgEl) return;
  const baglantiTestUrl = cfgEl.dataset.baglantiTestUrl;
  const aktifMod = cfgEl.dataset.aktifMod || "";

  const seciliModInput = document.getElementById("secili-mod");
  const devamBtn = document.getElementById("devam-btn");
  let testSonucu = { firmaId: null, mod: null, basarili: false };

  function guncelleButon() {
    const firmaRadio = document.querySelector("input[name='firma_id']:checked");
    const firmaId = firmaRadio ? firmaRadio.value : null;
    const mod = seciliModInput.value;
    const testGecerli =
      testSonucu.basarili &&
      String(testSonucu.firmaId) === String(firmaId) &&
      testSonucu.mod === mod;
    devamBtn.disabled = !(firmaId && mod && testGecerli);
  }

  function testSifirla() {
    testSonucu = { firmaId: null, mod: null, basarili: false };
    document.querySelectorAll(".test-sonuc").forEach((el) => {
      el.innerHTML = "";
    });
    document.querySelectorAll(".test-btn-text").forEach((el) => {
      el.innerHTML = '<i class="bi bi-plug me-1"></i>Bağlantıyı Test Et';
    });
    document.querySelectorAll(".test-btn").forEach((el) => {
      el.disabled = false;
    });
    guncelleButon();
  }

  function firmaAc(firmaId) {
    document
      .querySelectorAll(".mod-secenekler")
      .forEach((el) => el.classList.add("d-none"));
    document
      .querySelectorAll(".firma-kart")
      .forEach((el) => el.classList.remove("secili"));
    const panel = document.getElementById("modlar-" + firmaId);
    const kart = document.querySelector(
      ".firma-kart[data-firma-id='" + firmaId + "']"
    );
    if (kart) kart.classList.add("secili");
    if (panel) {
      panel.classList.remove("d-none");
      const ilkMod = panel.querySelector("input[type='radio']");
      if (ilkMod && !panel.querySelector("input[type='radio']:checked")) {
        ilkMod.checked = true;
      }
      const secilenMod = panel.querySelector("input[type='radio']:checked");
      seciliModInput.value = secilenMod ? secilenMod.value : "";
    }
    testSifirla();
  }

  document.querySelectorAll(".firma-kart").forEach((kart) => {
    kart.addEventListener("click", function () {
      const firmaId = this.dataset.firmaId;
      const radio = this.querySelector("input[name='firma_id']");
      if (radio) radio.checked = true;
      firmaAc(firmaId);
    });
  });

  document.querySelectorAll(".mod-btn").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const yeniMod = this.dataset.mod;
      if (seciliModInput.value !== yeniMod) {
        testSifirla();
      }
      seciliModInput.value = yeniMod;
      guncelleButon();
    });
  });

  // Bağlantı testi — AJAX
  document.querySelectorAll(".test-btn").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const firmaId = this.dataset.firma;
      const mod = seciliModInput.value;
      if (!mod) return;

      const kart = document.querySelector(
        ".firma-kart[data-firma-id='" + firmaId + "']"
      );
      const sonucEl = kart ? kart.querySelector(".test-sonuc") : null;
      const btnText = this.querySelector(".test-btn-text");
      this.disabled = true;
      btnText.innerHTML =
        '<span class="spinner-border spinner-border-sm me-1" role="status"></span>Test ediliyor...';
      if (sonucEl) sonucEl.innerHTML = "";

      const csrfToken = document.querySelector(
        "[name='csrfmiddlewaretoken']"
      ).value;
      const formData = new FormData();
      formData.append("firma_id", firmaId);
      formData.append("baglanti_modu", mod);
      formData.append("csrfmiddlewaretoken", csrfToken);

      fetch(baglantiTestUrl, { method: "POST", body: formData })
        .then((r) => {
          if (!r.ok || r.redirected) {
            throw new Error(
              "HTTP " + r.status + (r.redirected ? " (yönlendirme)" : "")
            );
          }
          return r.json();
        })
        .then((data) => {
          this.disabled = false;
          btnText.innerHTML =
            '<i class="bi bi-plug me-1"></i>Yeniden Test Et';
          if (data.basarili) {
            testSonucu = { firmaId: firmaId, mod: mod, basarili: true };
            if (sonucEl)
              sonucEl.innerHTML =
                '<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i>' +
                (data.sunucu || "Bağlantı başarılı") +
                "</span>";
          } else {
            testSonucu = { firmaId: null, mod: null, basarili: false };
            if (sonucEl)
              sonucEl.innerHTML =
                '<span class="text-danger"><i class="bi bi-x-circle-fill me-1"></i>' +
                (data.mesaj || "Bağlantı hatası") +
                "</span>";
          }
          guncelleButon();
        })
        .catch((err) => {
          this.disabled = false;
          btnText.innerHTML =
            '<i class="bi bi-plug me-1"></i>Yeniden Test Et';
          testSonucu = { firmaId: null, mod: null, basarili: false };
          const errMsg = err && err.message ? err.message : "Bağlantı hatası";
          if (sonucEl)
            sonucEl.innerHTML =
              '<span class="text-danger"><i class="bi bi-x-circle-fill me-1"></i>' +
              errMsg +
              "</span>";
          guncelleButon();
        });
    });
  });

  const seciliFirmaRadio = document.querySelector(
    "input[name='firma_id']:checked"
  );
  if (seciliFirmaRadio) {
    firmaAc(seciliFirmaRadio.value);
    if (aktifMod) {
      const modRadio = document.querySelector(
        "input[name='mod_" +
          seciliFirmaRadio.value +
          "'][value='" +
          aktifMod +
          "']"
      );
      if (modRadio) {
        modRadio.checked = true;
        seciliModInput.value = aktifMod;
      }
    }
    guncelleButon();
  }
})();
