// FMPS Teacher My Classes - real API data only

document.addEventListener("DOMContentLoaded", function () {
    const API_BASE = "http://127.0.0.1:5000/api";
    const SERVER_BASE = "http://127.0.0.1:5000";
    const token = localStorage.getItem("fmps_access_token");

    const classGrid = document.getElementById("classGrid");
    const noResult = document.getElementById("noResult");
    const classSearch = document.getElementById("classSearch");
    const topSearch = document.getElementById("topSearch");
    const semesterFilter = document.getElementById("semesterFilter");
    const themeToggle = document.getElementById("themeToggle");

    let teacherClasses = [];

    preparePage();
    bindEvents();

    if (!token) {
        window.location.replace("teacher-login.html");
        return;
    }

    loadClasses();

    async function loadClasses() {
        try {
            const response = await fetch(API_BASE + "/teachers/me/classes", {
                headers: {
                    Authorization: "Bearer " + token,
                    Accept: "application/json"
                }
            });

            const result = await response.json();

            if (response.status === 401) {
                clearSession();
                window.location.replace("teacher-login.html");
                return;
            }

            if (!response.ok || !result.success) {
                throw new Error(result.message || "Unable to load classes");
            }

            const data = result.data || {};
            teacherClasses = Array.isArray(data.classes) ? data.classes : [];

            renderProfile(data.teacher || {});
            renderStats(data.stats || {});
            renderSemesterOptions();
            filterAndRender();
        } catch (error) {
            console.error("Teacher classes error:", error);
            showError(error.message);
        }
    }

    function preparePage() {
        if (classGrid) {
            classGrid.innerHTML = `
                <div class="no-result" style="display:block;grid-column:1/-1">
                    <i class="fa-solid fa-spinner fa-spin"></i>
                    <h5>Loading classes...</h5>
                </div>`;
        }

        setStat(1, "-");
        setStat(2, "-");
        setStat(3, "-");
        setStat(4, "-");

        applySavedTheme();
    }

    function bindEvents() {
        if (classSearch) classSearch.addEventListener("input", filterAndRender);

        if (topSearch) {
            topSearch.addEventListener("input", function () {
                if (classSearch) classSearch.value = topSearch.value;
                filterAndRender();
            });
        }

        if (semesterFilter) {
            semesterFilter.addEventListener("change", filterAndRender);
        }

        if (themeToggle) {
            themeToggle.addEventListener("click", function () {
                document.body.classList.toggle("dark");
                const isDark = document.body.classList.contains("dark");
                localStorage.setItem("theme", isDark ? "dark" : "light");
                updateThemeIcon();
            });
        }

        document.querySelectorAll('a[href="teacher-login.html"]').forEach(function (link) {
            link.addEventListener("click", clearSession);
        });
    }

    function renderStats(stats) {
        setStat(1, stats.assigned_subjects ?? 0);
        setStat(2, stats.today_classes ?? 0);
        setStat(3, stats.weekly_classes ?? 0);
        setStat(4, stats.department || "Not Assigned");
    }

    function setStat(position, value) {
        const element = document.querySelector(
            `.stats-grid .stat-card:nth-child(${position}) h3`
        );
        if (element) element.textContent = value;
    }

    function renderProfile(teacher) {
        const profile = document.querySelector(".profile");
        if (!profile) return;

        const name = teacher.full_name || "Teacher";
        const title = profile.querySelector("h6");
        const subtitle = profile.querySelector("small");
        const image = profile.querySelector("img");

        if (title) title.textContent = "Welcome, " + name;
        if (subtitle) subtitle.textContent = teacher.designation || "Faculty Member";

        if (image && teacher.photo_url) {
            image.src = photoUrl(teacher.photo_url);
            image.onerror = function () {
                image.onerror = null;
                image.src = "../../images/default-profile.png";
            };
        }
    }

    function renderSemesterOptions() {
        if (!semesterFilter) return;

        const semesters = [...new Set(
            teacherClasses
                .map(function (item) { return String(item.semester || "").trim(); })
                .filter(Boolean)
        )].sort(function (a, b) {
            return Number(a) - Number(b);
        });

        semesterFilter.innerHTML = '<option value="all">All Semesters</option>' +
            semesters.map(function (semester) {
                return `<option value="${escapeHtml(semester)}">Semester ${escapeHtml(semester)}</option>`;
            }).join("");
    }

    function filterAndRender() {
        if (!classGrid) return;

        const query = String(classSearch?.value || topSearch?.value || "")
            .trim()
            .toLowerCase();
        const semester = semesterFilter?.value || "all";

        const filtered = teacherClasses.filter(function (item) {
            const searchable = [
                item.subject_name,
                item.subject_code,
                item.semester,
                ...(item.sections || []),
                ...(item.rooms || [])
            ].join(" ").toLowerCase();

            const matchesSearch = searchable.includes(query);
            const matchesSemester = semester === "all" ||
                String(item.semester || "") === semester;

            return matchesSearch && matchesSemester;
        });

        if (!filtered.length) {
            classGrid.innerHTML = "";
            if (noResult) noResult.style.display = "block";
            return;
        }

        if (noResult) noResult.style.display = "none";
        classGrid.innerHTML = filtered.map(renderClassCard).join("");
    }

    function renderClassCard(item) {
        const semester = item.semester || "-";
        const sections = item.sections?.length ? item.sections.join(", ") : "Not Scheduled";
        const rooms = item.rooms?.length ? item.rooms.join(", ") : "Not Scheduled";
        const types = item.class_types?.length
            ? item.class_types.map(capitalize).join(", ")
            : "Not Scheduled";
        const status = item.status === "scheduled" ? "Scheduled" : "Assigned";

        return `
            <article class="subject-card">
                <div class="subject-card-head">
                    <i class="fa-solid fa-book-open"></i>
                    <h4>${escapeHtml(item.subject_name || "Unnamed Subject")}</h4>
                    <p>Semester ${escapeHtml(semester)} • Section ${escapeHtml(sections)}</p>
                </div>
                <div class="subject-card-body">
                    <div class="subject-details">
                        <div class="detail-box">
                            <small>Subject Code</small>
                            <strong>${escapeHtml(item.subject_code || "-")}</strong>
                        </div>
                        <div class="detail-box">
                            <small>Room</small>
                            <strong>${escapeHtml(rooms)}</strong>
                        </div>
                        <div class="detail-box">
                            <small>Weekly Classes</small>
                            <strong>${Number(item.weekly_classes || 0)} Classes</strong>
                        </div>
                        <div class="detail-box">
                            <small>Status</small>
                            <strong>${status}</strong>
                        </div>
                        <div class="detail-box">
                            <small>Class Type</small>
                            <strong>${escapeHtml(types)}</strong>
                        </div>
                        <div class="detail-box">
                            <small>Credits</small>
                            <strong>${item.credits ?? "-"}</strong>
                        </div>
                    </div>
                </div>
            </article>`;
    }

    function showError(message) {
        if (classGrid) classGrid.innerHTML = "";
        if (!noResult) return;

        noResult.style.display = "block";
        noResult.innerHTML = `
            <i class="fa-solid fa-triangle-exclamation"></i>
            <h5>Unable to load classes</h5>
            <p>${escapeHtml(message)}</p>`;
    }

    function applySavedTheme() {
        if (localStorage.getItem("theme") === "dark") {
            document.body.classList.add("dark");
        }
        updateThemeIcon();
    }

    function updateThemeIcon() {
        if (!themeToggle) return;
        const icon = themeToggle.querySelector("i");
        if (icon) {
            icon.className = document.body.classList.contains("dark")
                ? "fa-solid fa-sun"
                : "fa-solid fa-moon";
        }
    }

    function photoUrl(value) {
        const path = String(value || "").replace(/\\/g, "/").trim();
        if (/^https?:\/\//i.test(path)) return path;

        const withoutPrefix = path.replace(/^\/?uploads\//i, "");
        return SERVER_BASE + "/uploads/" + withoutPrefix.replace(/^\/+/, "");
    }

    function clearSession() {
        localStorage.removeItem("fmps_access_token");
        localStorage.removeItem("fmps_refresh_token");
        localStorage.removeItem("fmps_user");
    }

    function capitalize(value) {
        const text = String(value || "");
        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
