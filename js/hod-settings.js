"use strict";

/* HOD SETTINGS: account data from backend; preferences remain local because
   this backend has no settings table/endpoint. */
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    replaceSaveHandler();
    replaceResetHandler();
    loadAccountDetails();
  });

  function replaceSaveHandler() {
    const oldButton = document.getElementById("saveSettingsBtn");
    if (!oldButton) return;
    const button = oldButton.cloneNode(true);
    oldButton.replaceWith(button);
    button.addEventListener("click", function () {
      const settings = readSettingsFromPage();
      localStorage.setItem("hodSettings", JSON.stringify(settings));
      localStorage.setItem("hodTheme", settings.theme);
      const modal = document.getElementById("settingsSuccessModal");
      if (modal && window.bootstrap?.Modal) bootstrap.Modal.getOrCreateInstance(modal).show();
    });
  }

  function replaceResetHandler() {
    const oldButton = document.getElementById("resetSettingsBtn");
    if (!oldButton) return;
    const button = oldButton.cloneNode(true);
    oldButton.replaceWith(button);
    button.addEventListener("click", function () {
      localStorage.removeItem("hodSettings");
      localStorage.removeItem("hodTheme");
      window.location.reload();
    });
  }

  async function loadAccountDetails() {
    if (typeof API === "undefined" || typeof API.request !== "function") return;
    try {
      const response = await API.request("GET", "/hods/profile");
      if (!response?.success) throw new Error(response?.message || "Account details load nahi hui.");
      const profile = response.data || {};
      const section = document.getElementById("accountSettings");
      if (!section) return;
      const name = section.querySelector(".account-mini-profile h5");
      const email = section.querySelector(".account-mini-profile p");
      const role = section.querySelector(".account-role");
      const values = section.querySelectorAll(".setting-item > strong");
      if (name) name.textContent = profile.full_name || "--";
      if (email) email.textContent = profile.email || "--";
      if (role) role.textContent = `${String(profile.role || "HOD").toUpperCase()} • ${profile.is_active ? "Active" : "Inactive"}`;
      if (values[0]) values[0].textContent = profile.hod_code || "--";
      if (values[1]) values[1].textContent = profile.department || "--";
      if (values[2]) values[2].textContent = profile.email || "--";
      const image = section.querySelector(".account-mini-profile img");
      if (image && profile.photo_url) image.src = makePhotoUrl(profile.photo_url);
    } catch (error) {
      console.warn("HOD account details unavailable:", error.message);
    }
  }

  function readSettingsFromPage() {
    const checked = id => Boolean(document.getElementById(id)?.checked);
    const value = id => document.getElementById(id)?.value ?? "";
    return {
      theme: document.querySelector(".theme-option.active")?.dataset.theme || "light",
      compactMode: checked("compactMode"),
      animations: checked("animationSetting"),
      fontSize: value("fontSizeSetting"),
      notifications: { enabled: checked("enableNotifications"), leave: checked("leaveNotifications"), attendance: checked("attendanceNotifications"), notice: checked("noticeNotifications"), reports: checked("reportNotifications"), email: checked("emailNotifications") },
      privacy: { profileVisibility: value("profileVisibility"), showContact: checked("showContactInfo"), onlineStatus: checked("showOnlineStatus"), loginHistory: checked("loginHistory"), analytics: checked("usageAnalytics") },
      system: { language: value("languageSetting"), timeFormat: value("timeFormat"), dateFormat: value("dateFormat"), landingPage: value("defaultLandingPage"), rememberFilters: checked("rememberFilters"), autoRefresh: checked("autoRefresh") }
    };
  }

  function makePhotoUrl(path) { return /^https?:|^blob:|^data:/.test(path) ? path : `${API.baseUrl.replace(/\/api$/, "")}${path}`; }
})();