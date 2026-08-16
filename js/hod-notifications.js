"use strict";

/* ============================================================
   HOD NOTIFICATIONS
   Backend routes used:
   GET   /api/notifications
   PATCH /api/notifications/<id>/read
   PATCH /api/notifications/read-all
============================================================ */

let hodNotifications = [];
let filteredNotifications = [];
let selectedNotificationId = null;
let notificationPage = 1;
const NOTIFICATIONS_PER_PAGE = 8;

document.addEventListener("DOMContentLoaded", async function () {
    prepareNotificationPage();

    if (typeof API === "undefined" || typeof API.request !== "function") {
        showNotificationListMessage("Unable to connect with backend.", true);
        return;
    }

    const authenticated = await protectHodNotificationPage();
    if (!authenticated) return;

    bindNotificationFilters();
    bindNotificationActions();
    bindMarkAllButtons();
    bindThemeToggle();
    bindLogout();

    await loadHodNotifications();
});

function prepareNotificationPage() {
    setText("totalNotificationCount", 0);
    setText("unreadNotificationCount", 0);
    setText("readNotificationCount", 0);
    setText("importantNotificationCount", 0);

    const badge = document.getElementById("notificationCount");
    if (badge) {
        badge.textContent = "0";
        badge.style.display = "none";
    }

    showNotificationListMessage("Loading notifications...");

    /* No delete/clear-read endpoint exists in the supplied backend. */
    const clearReadButton = document.getElementById("clearReadBtn");
    if (clearReadButton) clearReadButton.style.display = "none";

    /* Notification model has no priority field. */
    const priorityFilter = document.getElementById("notificationPriorityFilter");
    if (priorityFilter) priorityFilter.style.display = "none";

    const priorityInput = document.getElementById("modalNotificationPriority");
    if (priorityInput?.closest(".col-md-6")) {
        priorityInput.closest(".col-md-6").style.display = "none";
    }

    const importantLabel = document.querySelector(
        "#importantNotificationCount + p"
    );
    if (importantLabel) importantLabel.textContent = "Notification Types";

    const deleteModal = document.getElementById("deleteNotificationModal");
    if (deleteModal) deleteModal.remove();
}

async function protectHodNotificationPage() {
    try {
        const token = localStorage.getItem("fmps_access_token");
        if (!token) {
            window.location.replace("hod-login.html");
            return false;
        }

        if (!API.auth || typeof API.auth.me !== "function") {
            throw new Error("Authentication service is unavailable.");
        }

        const response = await API.auth.me();
        let user = null;

        if (response?.data?.user) {
            user = response.data.user;
        }
        else if (response?.data) {
            user = response.data;
        }
        else if (response?.user) {
            user = response.user;
        }
        else {
            user = response;
        }

        const role = String(user?.role || "").trim().toLowerCase();

        if (!user || role !== "hod") {
            API.auth.logout?.();
            alert("Access denied. HOD account required.");
            window.location.replace("hod-login.html");
            return false;
        }

        if (user.is_active === false || user.is_active === 0) {
            API.auth.logout?.();
            alert("Your HOD account is inactive.");
            window.location.replace("hod-login.html");
            return false;
        }

        const profileName = document.querySelector(".profile span");
        if (profileName) {
            profileName.textContent = `Welcome, ${user.username || user.email || "HOD"}`;
        }

        return true;
    }
    catch (error) {
        console.error("HOD Notification Authentication Error:", error);
        API.auth?.logout?.();
        window.location.replace("hod-login.html");
        return false;
    }
}

async function loadHodNotifications() {
    try {
        const response = await API.request("GET", "/notifications");

        if (!response || response.success !== true) {
            throw new Error(response?.message || "Unable to load notifications.");
        }

        hodNotifications = Array.isArray(response.data) ? response.data : [];
        window.currentHodNotifications = hodNotifications;

        populateNotificationTypes();
        updateNotificationCounters(response.summary);
        renderTopNotificationDropdown();
        applyNotificationFilters();
    }
    catch (error) {
        console.error("HOD Notification Load Error:", error);
        hodNotifications = [];
        filteredNotifications = [];
        updateNotificationCounters();
        renderTopNotificationDropdown();
        showNotificationListMessage(
            error.message || "Unable to load notifications.",
            true
        );
    }
}

function populateNotificationTypes() {
    const select = document.getElementById("notificationTypeFilter");
    if (!select) return;

    const currentValue = select.value;
    const categories = [...new Set(
        hodNotifications
            .map(item => String(item.category || "general").trim().toLowerCase())
            .filter(Boolean)
    )].sort();

    select.innerHTML = '<option value="all">All Types</option>';

    categories.forEach(function (category) {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = formatLabel(category);
        select.appendChild(option);
    });

    if (categories.includes(currentValue)) select.value = currentValue;
}

function bindNotificationFilters() {
    const search = document.getElementById("notificationSearchInput");
    const globalSearch = document.getElementById("globalSearch");

    search?.addEventListener("input", function () {
        notificationPage = 1;
        applyNotificationFilters();
    });

    globalSearch?.addEventListener("input", function () {
        if (search) search.value = globalSearch.value;
        notificationPage = 1;
        applyNotificationFilters();
    });

    ["notificationStatusFilter", "notificationTypeFilter"].forEach(function (id) {
        document.getElementById(id)?.addEventListener("change", function () {
            notificationPage = 1;
            applyNotificationFilters();
        });
    });
}

function applyNotificationFilters() {
    const search = String(
        document.getElementById("notificationSearchInput")?.value || ""
    ).trim().toLowerCase();
    const status = String(
        document.getElementById("notificationStatusFilter")?.value || "all"
    ).toLowerCase();
    const category = String(
        document.getElementById("notificationTypeFilter")?.value || "all"
    ).toLowerCase();

    filteredNotifications = hodNotifications.filter(function (notification) {
        const searchable = [
            notification.title,
            notification.message,
            notification.category
        ].filter(Boolean).join(" ").toLowerCase();

        const currentStatus = notification.is_read ? "read" : "unread";
        const currentCategory = String(notification.category || "general").toLowerCase();

        return (
            (!search || searchable.includes(search)) &&
            (status === "all" || currentStatus === status) &&
            (category === "all" || currentCategory === category)
        );
    });

    const totalPages = Math.max(
        1,
        Math.ceil(filteredNotifications.length / NOTIFICATIONS_PER_PAGE)
    );
    if (notificationPage > totalPages) notificationPage = totalPages;

    renderNotificationList();
    renderNotificationPagination();
}

function renderNotificationList() {
    const list = document.getElementById("notificationList");
    if (!list) return;

    if (filteredNotifications.length === 0) {
        showNotificationListMessage("No matching notifications found.");
        setText("notificationResultInfo", "No matching notifications found");
        return;
    }

    const start = (notificationPage - 1) * NOTIFICATIONS_PER_PAGE;
    const visible = filteredNotifications.slice(
        start,
        start + NOTIFICATIONS_PER_PAGE
    );

    list.innerHTML = visible.map(function (notification) {
        const id = Number(notification.id);
        const category = String(notification.category || "general").toLowerCase();
        const unreadClass = notification.is_read ? "" : "unread";
        const status = notification.is_read ? "read" : "unread";

        return `
            <div class="notification-item ${unreadClass}"
                 data-id="${id}"
                 data-status="${status}"
                 data-type="${escapeHtml(category)}">

                <div class="notification-type-icon ${escapeHtml(getCategoryClass(category))}">
                    <i class="${escapeHtml(getCategoryIcon(category))}"></i>
                </div>

                <div class="notification-info">
                    <div class="notification-title-row">
                        <h5>
                            ${notification.is_read ? "" : '<span class="unread-dot me-2"></span>'}
                            ${escapeHtml(notification.title || "Notification")}
                        </h5>
                        <span class="notification-time">
                            ${escapeHtml(formatNotificationTime(notification.created_at))}
                        </span>
                    </div>

                    <p>${escapeHtml(notification.message || "No message available.")}</p>

                    <div class="notification-meta">
                        <span class="notification-category">
                            <i class="${escapeHtml(getCategoryIcon(category))}"></i>
                            ${escapeHtml(formatLabel(category))}
                        </span>
                        <span class="badge ${notification.is_read ? "bg-secondary" : "bg-primary"}">
                            ${notification.is_read ? "Read" : "Unread"}
                        </span>
                    </div>
                </div>

                <div class="notification-actions">
                    <button type="button"
                            class="notification-action-btn notification-view-btn viewNotificationBtn"
                            data-id="${id}"
                            title="View">
                        <i class="fa-solid fa-eye"></i>
                    </button>

                    ${notification.is_read ? "" : `
                        <button type="button"
                                class="notification-action-btn notification-read-btn markReadBtn"
                                data-id="${id}"
                                title="Mark as Read">
                            <i class="fa-solid fa-check"></i>
                        </button>
                    `}
                </div>
            </div>
        `;
    }).join("");

    const end = Math.min(start + visible.length, filteredNotifications.length);
    setText(
        "notificationResultInfo",
        `Showing ${start + 1}-${end} of ${filteredNotifications.length} notifications`
    );
}

function showNotificationListMessage(message, isError = false) {
    const list = document.getElementById("notificationList");
    if (!list) return;

    list.innerHTML = `
        <div class="text-center py-5 ${isError ? "text-danger" : "text-muted"}">
            <i class="fa-solid ${isError ? "fa-circle-exclamation" : "fa-bell-slash"} fa-2x mb-3"></i>
            <div>${escapeHtml(message)}</div>
        </div>
    `;
}

function updateNotificationCounters(summary) {
    const total = Number(summary?.total ?? hodNotifications.length) || 0;
    const unread = Number(
        summary?.unread ?? hodNotifications.filter(item => !item.is_read).length
    ) || 0;
    const read = Number(summary?.read ?? (total - unread)) || 0;
    const categories = new Set(
        hodNotifications.map(item => item.category || "general")
    ).size;

    setText("totalNotificationCount", total);
    setText("unreadNotificationCount", unread);
    setText("readNotificationCount", read);
    setText("importantNotificationCount", categories);

    const badge = document.getElementById("notificationCount");
    if (badge) {
        badge.textContent = String(unread);
        badge.style.display = unread > 0 ? "flex" : "none";
    }

    const markAllButton = document.getElementById("markAllReadBtn");
    if (markAllButton) markAllButton.disabled = unread === 0;
}

function renderTopNotificationDropdown() {
    const menu = document.querySelector(".notification-menu");
    if (!menu) return;

    const unread = hodNotifications.filter(item => !item.is_read).length;
    const latest = hodNotifications.slice(0, 4);

    const items = latest.length
        ? latest.map(function (notification) {
            return `
                <li>
                    <a href="#"
                       class="dropdown-item ${notification.is_read ? "" : "fw-semibold"} topNotificationItem"
                       data-id="${Number(notification.id)}">
                        ${getCategoryEmoji(notification.category)}
                        ${escapeHtml(notification.title || "Notification")}
                    </a>
                </li>
            `;
        }).join("")
        : '<li><div class="dropdown-item text-muted text-center">No notifications</div></li>';

    menu.innerHTML = `
        <li class="dropdown-header">
            Notifications
            ${unread ? `<span class="float-end">${unread} unread</span>` : ""}
        </li>
        ${items}
        <li><hr class="dropdown-divider"></li>
        <li>
            <a href="#" class="dropdown-item text-center" id="topMarkAllRead">
                Mark All as Read
            </a>
        </li>
    `;

    document.getElementById("topMarkAllRead")?.addEventListener("click", async function (event) {
        event.preventDefault();
        await markAllNotificationsRead(this);
    });

    menu.querySelectorAll(".topNotificationItem").forEach(function (item) {
        item.addEventListener("click", function (event) {
            event.preventDefault();
            openNotificationModal(Number(this.dataset.id));
        });
    });
}

function bindNotificationActions() {
    document.getElementById("notificationList")?.addEventListener("click", async function (event) {
        const viewButton = event.target.closest(".viewNotificationBtn");
        const readButton = event.target.closest(".markReadBtn");

        if (viewButton) {
            openNotificationModal(Number(viewButton.dataset.id));
            return;
        }

        if (readButton) {
            await markOneNotificationRead(Number(readButton.dataset.id), readButton);
        }
    });

    document.getElementById("modalMarkReadBtn")?.addEventListener("click", async function () {
        if (selectedNotificationId) {
            await markOneNotificationRead(selectedNotificationId, this);
            openNotificationModal(selectedNotificationId);
        }
    });
}

function openNotificationModal(notificationId) {
    const notification = hodNotifications.find(
        item => Number(item.id) === Number(notificationId)
    );
    if (!notification) return;

    selectedNotificationId = Number(notification.id);

    setInputValue("modalNotificationId", notification.id);
    setText("modalNotificationTitle", notification.title || "Notification");
    setInputValue("modalNotificationMessage", notification.message || "No message available.");
    setInputValue("modalNotificationType", formatLabel(notification.category || "general"));
    setInputValue("modalNotificationStatus", notification.is_read ? "Read" : "Unread");
    setText("modalNotificationTime", formatNotificationTime(notification.created_at));

    const markButton = document.getElementById("modalMarkReadBtn");
    if (markButton) markButton.style.display = notification.is_read ? "none" : "inline-block";

    const modalElement = document.getElementById("viewNotificationModal");
    if (modalElement && typeof bootstrap !== "undefined") {
        bootstrap.Modal.getOrCreateInstance(modalElement).show();
    }
}

async function markOneNotificationRead(notificationId, button) {
    if (!notificationId) return;

    const originalHtml = button?.innerHTML;
    if (button) button.disabled = true;

    try {
        const response = await API.request(
            "PATCH",
            `/notifications/${notificationId}/read`,
            {}
        );

        if (!response || response.success !== true) {
            throw new Error(response?.message || "Unable to mark notification as read.");
        }

        const notification = hodNotifications.find(
            item => Number(item.id) === Number(notificationId)
        );
        if (notification) notification.is_read = true;

        updateNotificationCounters();
        renderTopNotificationDropdown();
        applyNotificationFilters();
    }
    catch (error) {
        console.error("Mark Notification Read Error:", error);
        alert(error.message || "Unable to mark notification as read.");
    }
    finally {
        if (button) {
            button.disabled = false;
            if (originalHtml !== undefined) button.innerHTML = originalHtml;
        }
    }
}

function bindMarkAllButtons() {
    document.getElementById("markAllReadBtn")?.addEventListener("click", async function () {
        await markAllNotificationsRead(this);
    });
}

async function markAllNotificationsRead(button) {
    const unread = hodNotifications.filter(item => !item.is_read).length;
    if (unread === 0) return;

    const originalHtml = button?.innerHTML;
    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
    }

    try {
        const response = await API.request("PATCH", "/notifications/read-all", {});

        if (!response || response.success !== true) {
            throw new Error(response?.message || "Unable to mark all notifications as read.");
        }

        hodNotifications.forEach(item => {
            item.is_read = true;
        });

        updateNotificationCounters();
        renderTopNotificationDropdown();
        applyNotificationFilters();
    }
    catch (error) {
        console.error("Mark All Notifications Read Error:", error);
        alert(error.message || "Unable to mark all notifications as read.");
    }
    finally {
        if (button && button.isConnected) {
            button.disabled = false;
            if (originalHtml !== undefined) button.innerHTML = originalHtml;
        }
    }
}

function renderNotificationPagination() {
    const container = document.querySelector(".notification-pagination");
    if (!container) return;

    const totalPages = Math.max(
        1,
        Math.ceil(filteredNotifications.length / NOTIFICATIONS_PER_PAGE)
    );

    if (filteredNotifications.length <= NOTIFICATIONS_PER_PAGE) {
        container.innerHTML = "";
        return;
    }

    let pageButtons = "";
    for (let page = 1; page <= totalPages; page += 1) {
        pageButtons += `
            <button type="button"
                    class="notificationPageBtn ${page === notificationPage ? "active" : ""}"
                    data-page="${page}">${page}</button>
        `;
    }

    container.innerHTML = `
        <button type="button" id="notificationPrevBtn" ${notificationPage === 1 ? "disabled" : ""}>
            <i class="fa-solid fa-chevron-left"></i>
        </button>
        ${pageButtons}
        <button type="button" id="notificationNextBtn" ${notificationPage === totalPages ? "disabled" : ""}>
            <i class="fa-solid fa-chevron-right"></i>
        </button>
    `;

    container.querySelectorAll(".notificationPageBtn").forEach(function (button) {
        button.addEventListener("click", function () {
            notificationPage = Number(this.dataset.page) || 1;
            renderNotificationList();
            renderNotificationPagination();
        });
    });

    document.getElementById("notificationPrevBtn")?.addEventListener("click", function () {
        if (notificationPage > 1) notificationPage -= 1;
        renderNotificationList();
        renderNotificationPagination();
    });

    document.getElementById("notificationNextBtn")?.addEventListener("click", function () {
        if (notificationPage < totalPages) notificationPage += 1;
        renderNotificationList();
        renderNotificationPagination();
    });
}

function bindThemeToggle() {
    const button = document.getElementById("themeToggle");
    if (!button) return;

    const storedTheme = localStorage.getItem("fmps_theme");
    if (storedTheme === "dark") document.body.classList.add("dark-mode");
    updateThemeIcon(button);

    button.addEventListener("click", function () {
        document.body.classList.toggle("dark-mode");
        localStorage.setItem(
            "fmps_theme",
            document.body.classList.contains("dark-mode") ? "dark" : "light"
        );
        updateThemeIcon(button);
    });
}

function updateThemeIcon(button) {
    const icon = button.querySelector("i");
    if (!icon) return;
    icon.className = document.body.classList.contains("dark-mode")
        ? "fa-solid fa-sun"
        : "fa-solid fa-moon";
}

function bindLogout() {
    document.querySelectorAll('a[href="hod-login.html"]').forEach(function (link) {
        link.addEventListener("click", function (event) {
            event.preventDefault();
            API.auth?.logout?.();
            window.location.replace("hod-login.html");
        });
    });
}

function getCategoryClass(category) {
    const allowed = ["leave", "attendance", "notice", "faculty", "system", "report"];
    const value = String(category || "system").toLowerCase();
    return allowed.includes(value) ? value : "system";
}

function getCategoryIcon(category) {
    const icons = {
        leave: "fa-solid fa-file-circle-check",
        attendance: "fa-solid fa-calendar-check",
        notice: "fa-solid fa-bullhorn",
        faculty: "fa-solid fa-chalkboard-user",
        report: "fa-solid fa-chart-column",
        system: "fa-solid fa-gear",
        general: "fa-solid fa-bell"
    };
    return icons[String(category || "general").toLowerCase()] || icons.general;
}

function getCategoryEmoji(category) {
    const emojis = {
        leave: "📄",
        attendance: "✅",
        notice: "📢",
        faculty: "🎓",
        report: "📊",
        system: "⚙️",
        general: "🔔"
    };
    return emojis[String(category || "general").toLowerCase()] || emojis.general;
}

function formatNotificationTime(value) {
    if (!value) return "--";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);

    const difference = Date.now() - date.getTime();
    const minutes = Math.floor(difference / 60000);
    const hours = Math.floor(difference / 3600000);
    const days = Math.floor(difference / 86400000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
    if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
    if (days < 7) return `${days} day${days === 1 ? "" : "s"} ago`;

    return date.toLocaleString();
}

function formatLabel(value) {
    return String(value || "general")
        .replaceAll("_", " ")
        .replace(/\b\w/g, letter => letter.toUpperCase());
}

function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) element.textContent = String(value ?? "");
}

function setInputValue(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) element.value = String(value ?? "");
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}