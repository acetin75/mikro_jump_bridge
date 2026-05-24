// Mikro Sync — ortak script
document.addEventListener("DOMContentLoaded", function () {
  // Sidebar firma seçici otomatik submit
  var firmaSelect = document.querySelector("#sidebar-firma-form select[name=firma_id]");
  if (firmaSelect) {
    firmaSelect.addEventListener("change", function () {
      document.getElementById("sidebar-firma-form").submit();
    });
  }
});
