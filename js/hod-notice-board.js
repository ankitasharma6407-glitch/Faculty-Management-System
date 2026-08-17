"use strict";

/* ============================================================
   HOD NOTICE BOARD

   GET    /api/notices/hod
   POST   /api/notices/hod
   PATCH  /api/notices/hod/<notice_id>
   DELETE /api/notices/hod/<notice_id>
============================================================ */

(function () {
    const NOTICES_PER_PAGE = 6;

    let hodNotices = [];
    let filteredNotices = [];
    let noticePage = 1;
    let selectedNoticeId = null;
    let messageTimer = null;

    document.addEventListener("DOMContentLoaded", async function () {
        if (typeof API === "undefined" || typeof API.request !== "function") {
            showPageMessage("Unable to connect with backend. Check api.js.", true);
            showTableMessage("Unable to connect with backend.", true);
            return;
        }

        bindNoticeFilters();
        bindCreateNoticeForm();
        bindNoticeActions();
        bindPageControls();

        await Promise.all([
            loadHodNotices(),
            loadNoticeNotificationPreview()
        ]);
    });

    async function loadHodNotices() {
        showTableMessage("Loading notices...");
        setNoticeActionButtonsDisabled(true);

        try {
            const response = await API.request("GET", "/notices/hod");

            if (!response || response.success !== true) {
                throw new Error(response?.message || "Unable to load notices.");
            }

            hodNotices = Array.isArray(response.data) ? response.data : [];
            window.currentHodNotices = hodNotices;

            const department = response.department || "your department";
            setText("noticeDepartmentLabel", `Showing notices for ${department}.`);
            updateNoticeStatistics(response.summary || {});

            noticePage = 1;
            applyNoticeFilters();
        }
        catch (error) {
            console.error("HOD Notice Load Error:", error);
            hodNotices = [];
            filteredNotices = [];
            updateNoticeStatistics({});
            showTableMessage(error.message || "Unable to load notices.", true);
            setText("noticeResultInfo", "0 notices");
            renderNoticePagination();
            showPageMessage(error.message || "Unable to load notices.", true);
        }
        finally {
            setNoticeActionButtonsDisabled(false);
        }
    }

    function updateNoticeStatistics(summary) {
        const total = Number(summary.total ?? hodNotices.length) || 0;
        const published = Number(
            summary.published ?? hodNotices.filter(item => normalize(item.status) === "published").length
        ) || 0;
        const draft = Number(
            summary.draft ?? hodNotices.filter(item => normalize(item.status) === "draft").length
        ) || 0;
        const urgent = Number(
            summary.urgent ?? hodNotices.filter(item => normalize(item.priority) === "urgent").length
        ) || 0;

        setText("totalNoticeCount", total);
        setText("publishedNoticeCount", published);
        setText("draftNoticeCount", draft);
        setText("urgentNoticeCount", urgent);
    }

    function bindNoticeFilters() {
        const pageSearch = document.getElementById("noticeSearchInput");
        const topSearch = document.getElementById("topSearch");

        pageSearch?.addEventListener("input", function () {
            if (topSearch) topSearch.value = pageSearch.value;
            noticePage = 1;
            applyNoticeFilters();
        });

        topSearch?.addEventListener("input", function () {
            if (pageSearch) pageSearch.value = topSearch.value;
            noticePage = 1;
            applyNoticeFilters();
        });

        ["noticeStatusFilter", "noticePriorityFilter"].forEach(function (id) {
            document.getElementById(id)?.addEventListener("change", function () {
                noticePage = 1;
                applyNoticeFilters();
            });
        });
    }

    function applyNoticeFilters() {
        const search = normalize(document.getElementById("noticeSearchInput")?.value);
        const status = normalize(document.getElementById("noticeStatusFilter")?.value || "all");
        const priority = normalize(document.getElementById("noticePriorityFilter")?.value || "all");

        filteredNotices = hodNotices.filter(function (notice) {
            const searchable = [
                notice.title,
                notice.message,
                notice.category,
                notice.audience,
                notice.priority,
                notice.status,
                notice.source
            ].map(value => String(value ?? "")).join(" ").toLowerCase();

            const matchesSearch = !search || searchable.includes(search);
            const matchesStatus = status === "all" || normalize(notice.status) === status;
            const matchesPriority = priority === "all" || normalize(notice.priority) === priority;

            return matchesSearch && matchesStatus && matchesPriority;
        });

        const totalPages = Math.max(1, Math.ceil(filteredNotices.length / NOTICES_PER_PAGE));
        if (noticePage > totalPages) noticePage = totalPages;

        renderNoticeRows();
        renderNoticePagination();
    }

    function renderNoticeRows() {
        const body = document.getElementById("noticeTableBody");
        if (!body) return;

        if (filteredNotices.length === 0) {
            showTableMessage("No matching notices found.");
            setText("noticeResultInfo", "No matching notices found");
            return;
        }

        const start = (noticePage - 1) * NOTICES_PER_PAGE;
        const visibleNotices = filteredNotices.slice(start, start + NOTICES_PER_PAGE);

        body.innerHTML = visibleNotices.map(function (notice) {
            const noticeId = Number(notice.id);
            const priority = safeEnum(notice.priority, ["normal", "important", "urgent"], "normal");
            const status = safeEnum(notice.status, ["draft", "published", "archived"], "draft");
            const canEdit = notice.can_edit === true;
            const canDelete = notice.can_delete === true;

            return `
                <tr data-notice-id="${noticeId}">
                    <td>
                        <div class="notice-title-box">
                            <div class="notice-mini-icon">
                                <i class="fa-solid ${getCategoryIcon(notice.category)}"></i>
                            </div>
                            <div>
                                <strong>${escapeHtml(notice.title || "Untitled Notice")}</strong>
                                <small>N${String(noticeId).padStart(3, "0")} • ${escapeHtml(formatLabel(notice.category || "general"))}</small>
                            </div>
                        </div>
                    </td>
                    <td>${escapeHtml(formatAudience(notice.audience))}</td>
                    <td>${getPriorityBadge(priority)}</td>
                    <td>${escapeHtml(formatDate(notice.created_at, true))}</td>
                    <td>${escapeHtml(formatDate(notice.expiry_date))}</td>
                    <td>${getStatusBadge(status)}</td>
                    <td>
                        <div class="notice-actions">
                            <button type="button" class="notice-action-btn notice-view-btn viewNoticeBtn" data-notice-id="${noticeId}" title="View">
                                <i class="fa-solid fa-eye"></i>
                            </button>
                            ${canEdit ? `
                                <button type="button" class="notice-action-btn notice-edit-btn editNoticeBtn" data-notice-id="${noticeId}" title="Edit">
                                    <i class="fa-solid fa-pen"></i>
                                </button>
                            ` : ""}
                            ${canDelete ? `
                                <button type="button" class="notice-action-btn notice-delete-btn deleteNoticeBtn" data-notice-id="${noticeId}" title="Delete">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            ` : ""}
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        const end = Math.min(start + NOTICES_PER_PAGE, filteredNotices.length);
        setText(
            "noticeResultInfo",
            `Showing ${start + 1}-${end} of ${filteredNotices.length} notice${filteredNotices.length === 1 ? "" : "s"}`
        );
    }

    function showTableMessage(message, isError = false) {
        const body = document.getElementById("noticeTableBody");
        if (!body) return;

        body.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 ${isError ? "text-danger" : "text-muted"}">
                    ${escapeHtml(message)}
                </td>
            </tr>
        `;
    }

    function renderNoticePagination() {
        const container = document.getElementById("noticePagination");
        if (!container) return;

        const totalPages = Math.max(1, Math.ceil(filteredNotices.length / NOTICES_PER_PAGE));
        const pageButtons = [];

        for (let page = 1; page <= totalPages; page += 1) {
            pageButtons.push(`
                <button type="button" class="noticePageBtn ${page === noticePage ? "active" : ""}" data-page="${page}">
                    ${page}
                </button>
            `);
        }

        container.innerHTML = `
            <button type="button" id="noticePrevBtn" ${noticePage === 1 ? "disabled" : ""} title="Previous">
                <i class="fa-solid fa-angle-left"></i>
            </button>
            ${pageButtons.join("")}
            <button type="button" id="noticeNextBtn" ${noticePage === totalPages ? "disabled" : ""} title="Next">
                <i class="fa-solid fa-angle-right"></i>
            </button>
        `;

        container.querySelectorAll(".noticePageBtn").forEach(function (button) {
            button.addEventListener("click", function () {
                noticePage = Number(this.dataset.page) || 1;
                renderNoticeRows();
                renderNoticePagination();
            });
        });

        document.getElementById("noticePrevBtn")?.addEventListener("click", function () {
            if (noticePage > 1) noticePage -= 1;
            renderNoticeRows();
            renderNoticePagination();
        });

        document.getElementById("noticeNextBtn")?.addEventListener("click", function () {
            if (noticePage < totalPages) noticePage += 1;
            renderNoticeRows();
            renderNoticePagination();
        });
    }

    function bindCreateNoticeForm() {
        const form = document.getElementById("createNoticeForm");
        const description = document.getElementById("noticeDescription");

        description?.addEventListener("input", function () {
            setText("noticeCharacterCount", description.value.length);
        });

        form?.addEventListener("submit", createHodNotice);

        document.getElementById("clearNoticeFormBtn")?.addEventListener("click", function () {
            resetCreateNoticeForm();
        });
    }

    async function createHodNotice(event) {
        event.preventDefault();

        const form = document.getElementById("createNoticeForm");
        if (!form?.checkValidity()) {
            form?.reportValidity();
            return;
        }

        const payload = {
            title: document.getElementById("noticeTitle")?.value.trim() || "",
            message: document.getElementById("noticeDescription")?.value.trim() || "",
            category: document.getElementById("noticeCategory")?.value || "general",
            audience: document.getElementById("noticeAudience")?.value || "all",
            priority: document.getElementById("noticePriority")?.value || "normal",
            status: document.getElementById("noticeStatus")?.value || "published",
            expiry_date: document.getElementById("noticeExpiryDate")?.value || ""
        };

        const button = document.getElementById("publishNoticeBtn");
        setButtonLoading(button, true, "Saving...");

        try {
            const response = await API.request("POST", "/notices/hod", payload);

            if (!response || response.success !== true) {
                throw new Error(response?.message || "Unable to create notice.");
            }

            resetCreateNoticeForm();
            showPageMessage(response.message || "Notice created successfully.");
            await loadHodNotices();
        }
        catch (error) {
            console.error("HOD Notice Create Error:", error);
            showPageMessage(error.message || "Unable to create notice.", true);
        }
        finally {
            setButtonLoading(button, false);
        }
    }

    function resetCreateNoticeForm() {
        document.getElementById("createNoticeForm")?.reset();
        setInputValue("noticePriority", "normal");
        setInputValue("noticeStatus", "published");
        setInputValue("noticeAudience", "all");
        setText("noticeCharacterCount", "0");
    }

    function bindNoticeActions() {
        document.getElementById("noticeTable")?.addEventListener("click", function (event) {
            const viewButton = event.target.closest(".viewNoticeBtn");
            const editButton = event.target.closest(".editNoticeBtn");
            const deleteButton = event.target.closest(".deleteNoticeBtn");

            if (viewButton) openViewNoticeModal(Number(viewButton.dataset.noticeId));
            if (editButton) openEditNoticeModal(Number(editButton.dataset.noticeId));
            if (deleteButton) openDeleteNoticeModal(Number(deleteButton.dataset.noticeId));
        });

        document.getElementById("saveNoticeChangesBtn")?.addEventListener("click", updateHodNotice);
        document.getElementById("confirmDeleteNoticeBtn")?.addEventListener("click", deleteHodNotice);
    }

    function openViewNoticeModal(noticeId) {
        const notice = findNotice(noticeId);
        if (!notice) return;

        setText("viewNoticeTitle", notice.title || "Untitled Notice");
        setText("viewNoticeCategory", formatLabel(notice.category || "general"));
        setInputValue("viewNoticeId", `N${String(notice.id).padStart(3, "0")}`);
        setInputValue("viewNoticeSource", formatLabel(notice.source || "system"));
        setInputValue("viewNoticeAudience", formatAudience(notice.audience));
        setInputValue("viewNoticePriority", formatLabel(notice.priority || "normal"));
        setInputValue("viewNoticeStatus", formatLabel(notice.status || "draft"));
        setInputValue("viewNoticeCreated", formatDate(notice.created_at, true));
        setInputValue("viewNoticeExpiry", formatDate(notice.expiry_date));
        setInputValue("viewNoticeDescription", notice.message || "No description available.");

        bootstrap.Modal.getOrCreateInstance(document.getElementById("viewNoticeModal")).show();
    }

    function openEditNoticeModal(noticeId) {
        const notice = findNotice(noticeId);
        if (!notice || notice.can_edit !== true) {
            showPageMessage("You can edit only notices created by you.", true);
            return;
        }

        selectedNoticeId = Number(notice.id);
        setInputValue("editNoticeId", notice.id);
        setInputValue("editNoticeTitle", notice.title || "");
        setInputValue("editNoticeCategory", normalize(notice.category) || "general");
        setInputValue("editNoticeAudience", normalize(notice.audience) || "all");
        setInputValue("editNoticePriority", normalize(notice.priority) || "normal");
        setInputValue("editNoticeStatus", normalize(notice.status) || "draft");
        setInputValue("editNoticeExpiryDate", toDateInputValue(notice.expiry_date));
        setInputValue("editNoticeDescription", notice.message || "");

        bootstrap.Modal.getOrCreateInstance(document.getElementById("editNoticeModal")).show();
    }

    async function updateHodNotice() {
        const form = document.getElementById("editNoticeForm");
        if (!selectedNoticeId || !form?.checkValidity()) {
            form?.reportValidity();
            return;
        }

        const payload = {
            title: document.getElementById("editNoticeTitle")?.value.trim() || "",
            message: document.getElementById("editNoticeDescription")?.value.trim() || "",
            category: document.getElementById("editNoticeCategory")?.value || "general",
            audience: document.getElementById("editNoticeAudience")?.value || "all",
            priority: document.getElementById("editNoticePriority")?.value || "normal",
            status: document.getElementById("editNoticeStatus")?.value || "draft",
            expiry_date: document.getElementById("editNoticeExpiryDate")?.value || ""
        };

        const button = document.getElementById("saveNoticeChangesBtn");
        setButtonLoading(button, true, "Saving...");

        try {
            const response = await API.request(
                "PATCH",
                `/notices/hod/${selectedNoticeId}`,
                payload
            );

            if (!response || response.success !== true) {
                throw new Error(response?.message || "Unable to update notice.");
            }

            bootstrap.Modal.getInstance(document.getElementById("editNoticeModal"))?.hide();
            selectedNoticeId = null;
            showPageMessage(response.message || "Notice updated successfully.");
            await loadHodNotices();
        }
        catch (error) {
            console.error("HOD Notice Update Error:", error);
            showPageMessage(error.message || "Unable to update notice.", true);
        }
        finally {
            setButtonLoading(button, false);
        }
    }

    function openDeleteNoticeModal(noticeId) {
        const notice = findNotice(noticeId);
        if (!notice || notice.can_delete !== true) {
            showPageMessage("You can delete only notices created by you.", true);
            return;
        }

        selectedNoticeId = Number(notice.id);
        setText("deleteNoticeTitle", notice.title || "this notice");
        bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteNoticeModal")).show();
    }

    async function deleteHodNotice() {
        if (!selectedNoticeId) return;

        const button = document.getElementById("confirmDeleteNoticeBtn");
        setButtonLoading(button, true, "Deleting...");

        try {
            const response = await API.request(
                "DELETE",
                `/notices/hod/${selectedNoticeId}`
            );

            if (!response || response.success !== true) {
                throw new Error(response?.message || "Unable to delete notice.");
            }

            bootstrap.Modal.getInstance(document.getElementById("deleteNoticeModal"))?.hide();
            selectedNoticeId = null;
            showPageMessage(response.message || "Notice deleted successfully.");
            await loadHodNotices();
        }
        catch (error) {
            console.error("HOD Notice Delete Error:", error);
            showPageMessage(error.message || "Unable to delete notice.", true);
        }
        finally {
            setButtonLoading(button, false);
        }
    }

    function bindPageControls() {
        document.getElementById("scrollCreateNoticeBtn")?.addEventListener("click", function () {
            document.getElementById("createNoticeSection")?.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
            window.setTimeout(() => document.getElementById("noticeTitle")?.focus(), 450);
        });
    }

    async function loadNoticeNotificationPreview() {
        try {
            const response = await API.request("GET", "/notifications");
            if (!response || response.success !== true) return;

            const notifications = Array.isArray(response.data) ? response.data : [];
            const unread = Number(
                response.summary?.unread ?? notifications.filter(item => !item.is_read).length
            ) || 0;

            const badge = document.getElementById("notificationCount");
            if (badge) {
                badge.textContent = String(unread);
                badge.style.display = unread > 0 ? "flex" : "none";
            }

            const menu = document.querySelector(".notification-menu");
            if (!menu) return;

            const latest = notifications.slice(0, 4);
            const items = latest.length
                ? latest.map(function (notification) {
                    return `
                        <li>
                            <a class="dropdown-item ${notification.is_read ? "" : "fw-semibold"}" href="notification.html">
                                <i class="fa-solid fa-bell me-2"></i>${escapeHtml(notification.title || "Notification")}
                            </a>
                        </li>
                    `;
                }).join("")
                : '<li><div class="dropdown-item text-muted text-center">No notifications</div></li>';

            menu.innerHTML = `
                <li class="dropdown-header">Notifications${unread ? `<span class="float-end">${unread} unread</span>` : ""}</li>
                ${items}
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item text-center" href="notification.html">View All Notifications</a></li>
            `;
        }
        catch (error) {
            console.warn("Notification preview could not be loaded:", error);
        }
    }

    function findNotice(noticeId) {
        return hodNotices.find(item => Number(item.id) === Number(noticeId));
    }

    function getPriorityBadge(priority) {
        const icons = {
            normal: "fa-circle",
            important: "fa-circle-exclamation",
            urgent: "fa-triangle-exclamation"
        };

        return `
            <span class="notice-badge priority-${priority}">
                <i class="fa-solid ${icons[priority]}"></i>${escapeHtml(formatLabel(priority))}
            </span>
        `;
    }

    function getStatusBadge(status) {
        const icons = {
            published: "fa-circle-check",
            draft: "fa-file-pen",
            archived: "fa-box-archive"
        };

        return `
            <span class="notice-badge status-${status}">
                <i class="fa-solid ${icons[status]}"></i>${escapeHtml(formatLabel(status))}
            </span>
        `;
    }

    function getCategoryIcon(category) {
        const icons = {
            general: "fa-bullhorn",
            academic: "fa-book-open",
            examination: "fa-file-pen",
            event: "fa-calendar-star",
            placement: "fa-briefcase"
        };
        return icons[normalize(category)] || icons.general;
    }

    function formatAudience(value) {
        const labels = {
            all: "Everyone",
            teacher: "Teachers",
            student: "Students",
            hod: "HOD"
        };
        return labels[normalize(value)] || formatLabel(value || "all");
    }

    function formatDate(value, includeTime = false) {
        if (!value) return "--";

        const raw = String(value);
        const dateOnlyMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);

        if (dateOnlyMatch) {
            const date = new Date(
                Number(dateOnlyMatch[1]),
                Number(dateOnlyMatch[2]) - 1,
                Number(dateOnlyMatch[3])
            );
            return date.toLocaleDateString("en-IN", {
                day: "2-digit",
                month: "short",
                year: "numeric"
            });
        }

        const date = new Date(raw);
        if (Number.isNaN(date.getTime())) return raw;

        const options = {
            day: "2-digit",
            month: "short",
            year: "numeric"
        };

        if (includeTime) {
            options.hour = "2-digit";
            options.minute = "2-digit";
        }

        return date.toLocaleString("en-IN", options);
    }

    function toDateInputValue(value) {
        if (!value) return "";
        const match = String(value).match(/^(\d{4}-\d{2}-\d{2})/);
        return match ? match[1] : "";
    }

    function showPageMessage(message, isError = false) {
        const element = document.getElementById("noticePageMessage");
        if (!element) return;

        window.clearTimeout(messageTimer);
        element.className = `alert notice-form-message ${isError ? "alert-danger" : "alert-success"}`;
        element.textContent = String(message || "");
        element.style.display = "block";
        element.scrollIntoView({ behavior: "smooth", block: "nearest" });

        messageTimer = window.setTimeout(function () {
            element.style.display = "none";
        }, 5000);
    }

    function setNoticeActionButtonsDisabled(disabled) {
        ["publishNoticeBtn", "clearNoticeFormBtn"].forEach(function (id) {
            const button = document.getElementById(id);
            if (button) button.disabled = disabled;
        });
    }

    function setButtonLoading(button, loading, loadingText = "Please wait...") {
        if (!button) return;

        if (loading) {
            button.dataset.originalHtml = button.innerHTML;
            button.disabled = true;
            button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${escapeHtml(loadingText)}`;
        }
        else {
            button.disabled = false;
            if (button.dataset.originalHtml) {
                button.innerHTML = button.dataset.originalHtml;
                delete button.dataset.originalHtml;
            }
        }
    }

    function setText(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) element.textContent = String(value ?? "");
    }

    function setInputValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) element.value = String(value ?? "");
    }

    function normalize(value) {
        return String(value ?? "").trim().toLowerCase();
    }

    function safeEnum(value, allowed, fallback) {
        const normalized = normalize(value);
        return allowed.includes(normalized) ? normalized : fallback;
    }

    function formatLabel(value) {
        return String(value || "")
            .replaceAll("_", " ")
            .replace(/\b\w/g, letter => letter.toUpperCase());
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }
})();