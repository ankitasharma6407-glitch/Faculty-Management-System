"use strict";

/* ============================================================
   HOD ACADEMIC CALENDAR

   GET    /api/academic-events/hod
   POST   /api/academic-events/hod
   PATCH  /api/academic-events/hod/<event_id>
   DELETE /api/academic-events/hod/<event_id>
============================================================ */

(function () {
    let academicCalendar = null;
    let hodAcademicEvents = [];
    let filteredAcademicEvents = [];
    let currentDepartment = "Your department";
    let selectedAcademicEventId = null;
    let calendarMessageTimer = null;

    document.addEventListener("DOMContentLoaded", async function () {
        if (typeof API === "undefined" || typeof API.request !== "function") {
            showCalendarMessage("Unable to connect with backend. Check api.js.", true);
            showCalendarFallback("Unable to connect with backend.", true);
            return;
        }

        if (typeof FullCalendar === "undefined") {
            showCalendarMessage("Calendar library could not be loaded.", true);
            showCalendarFallback("Calendar library could not be loaded.", true);
            return;
        }

        initializeAcademicCalendar();
        bindCalendarFilters();
        bindAddEventControls();
        bindEventActionControls();
        bindCalendarPageControls();

        await Promise.all([
            loadHodAcademicEvents(),
            loadCalendarNotificationPreview()
        ]);
    });

    function initializeAcademicCalendar() {
        const calendarElement = document.getElementById("academicCalendar");
        if (!calendarElement) return;

        academicCalendar = new FullCalendar.Calendar(calendarElement, {
            initialView: "dayGridMonth",
            height: "auto",
            firstDay: 1,
            dayMaxEvents: 3,
            displayEventTime: false,
            headerToolbar: {
                left: "prev,next",
                center: "title",
                right: "dayGridMonth,listMonth"
            },
            buttonText: {
                month: "Month",
                list: "List"
            },
            dateClick: function (info) {
                openAddEventModal(info.dateStr);
            },
            eventClick: function (info) {
                info.jsEvent.preventDefault();
                openEventDetailsModal(Number(info.event.id));
            },
            eventDidMount: function (info) {
                info.el.title = info.event.title;
            },
            noEventsContent: "No academic events found"
        });

        academicCalendar.render();
    }

    async function loadHodAcademicEvents() {
        setCalendarButtonsDisabled(true);

        try {
            const response = await API.request("GET", "/academic-events/hod");

            if (!response || response.success !== true) {
                throw new Error(response?.message || "Unable to load academic events.");
            }

            hodAcademicEvents = Array.isArray(response.data) ? response.data : [];
            window.currentHodAcademicEvents = hodAcademicEvents;

            currentDepartment = response.department || "Your department";
            setText("calendarDepartmentLabel", `Showing global and ${currentDepartment} events.`);
            setInputValue("eventDepartment", currentDepartment);

            updateCalendarStatistics(response.summary || {});
            populateEventTypeFilter();
            renderEventCategories();
            applyCalendarFilters();
        }
        catch (error) {
            console.error("HOD Academic Calendar Load Error:", error);
            hodAcademicEvents = [];
            filteredAcademicEvents = [];
            updateCalendarStatistics({});
            renderEventCategories();
            refreshFullCalendarEvents();
            renderUpcomingEvents();
            showCalendarMessage(error.message || "Unable to load academic events.", true);
        }
        finally {
            setCalendarButtonsDisabled(false);
        }
    }

    function updateCalendarStatistics(summary) {
        const total = Number(summary.total ?? hodAcademicEvents.length) || 0;
        const upcoming = Number(
            summary.upcoming ?? hodAcademicEvents.filter(event => normalize(event.status) === "upcoming").length
        ) || 0;
        const ongoing = Number(
            summary.ongoing ?? hodAcademicEvents.filter(event => normalize(event.status) === "ongoing").length
        ) || 0;
        const completed = Number(
            summary.completed ?? hodAcademicEvents.filter(event => normalize(event.status) === "completed").length
        ) || 0;

        setText("totalEventCount", total);
        setText("upcomingEventCount", upcoming);
        setText("ongoingEventCount", ongoing);
        setText("completedEventCount", completed);
    }

    function populateEventTypeFilter() {
        const select = document.getElementById("eventTypeFilter");
        if (!select) return;

        const selectedValue = select.value || "all";
        const eventTypes = [...new Set(
            hodAcademicEvents
                .map(event => normalize(event.event_type) || "event")
                .filter(Boolean)
        )].sort();

        select.innerHTML = '<option value="all">All Event Types</option>';

        eventTypes.forEach(function (eventType) {
            const option = document.createElement("option");
            option.value = eventType;
            option.textContent = formatEventType(eventType);
            select.appendChild(option);
        });

        select.value = eventTypes.includes(selectedValue) ? selectedValue : "all";
    }

    function renderEventCategories() {
        const container = document.getElementById("eventCategoryList");
        if (!container) return;

        if (hodAcademicEvents.length === 0) {
            container.innerHTML = '<div class="text-muted text-center py-3">No event categories found.</div>';
            return;
        }

        const counts = hodAcademicEvents.reduce(function (result, event) {
            const eventType = normalize(event.event_type) || "event";
            result[eventType] = (result[eventType] || 0) + 1;
            return result;
        }, {});

        container.innerHTML = Object.entries(counts)
            .sort((first, second) => first[0].localeCompare(second[0]))
            .map(function ([eventType, count]) {
                const color = getEventColor(eventType);
                return `
                    <div class="event-category">
                        <div class="category-left">
                            <span class="category-dot" style="background:${color};"></span>
                            ${escapeHtml(formatEventType(eventType))}
                        </div>
                        <span class="badge" style="background:${color};">${count}</span>
                    </div>
                `;
            }).join("");
    }

    function bindCalendarFilters() {
        const calendarSearch = document.getElementById("calendarSearchInput");
        const topSearch = document.getElementById("topSearch");

        calendarSearch?.addEventListener("input", function () {
            if (topSearch) topSearch.value = calendarSearch.value;
            applyCalendarFilters();
        });

        topSearch?.addEventListener("input", function () {
            if (calendarSearch) calendarSearch.value = topSearch.value;
            applyCalendarFilters();
        });

        document.getElementById("eventTypeFilter")?.addEventListener("change", applyCalendarFilters);
    }

    function applyCalendarFilters() {
        const search = normalize(document.getElementById("calendarSearchInput")?.value);
        const eventType = normalize(document.getElementById("eventTypeFilter")?.value || "all");

        filteredAcademicEvents = hodAcademicEvents.filter(function (event) {
            const searchable = [
                event.title,
                event.description,
                event.event_type,
                event.department,
                event.status,
                event.scope
            ].map(value => String(value ?? "")).join(" ").toLowerCase();

            const matchesSearch = !search || searchable.includes(search);
            const matchesType = eventType === "all" || normalize(event.event_type) === eventType;
            return matchesSearch && matchesType;
        });

        refreshFullCalendarEvents();
        renderUpcomingEvents();
    }

    function refreshFullCalendarEvents() {
        if (!academicCalendar) return;

        academicCalendar.removeAllEvents();
        academicCalendar.addEventSource(
            filteredAcademicEvents.map(toFullCalendarEvent)
        );
    }

    function toFullCalendarEvent(event) {
        const eventType = normalize(event.event_type) || "event";
        const color = getEventColor(eventType);

        return {
            id: String(event.id),
            title: event.title || "Untitled Event",
            start: event.start_date,
            end: inclusiveEndToExclusive(event.end_date),
            allDay: true,
            backgroundColor: color,
            borderColor: color,
            textColor: "#ffffff",
            extendedProps: {
                eventType,
                status: event.status,
                department: event.department,
                scope: event.scope
            }
        };
    }

    function renderUpcomingEvents() {
        const container = document.getElementById("upcomingEventsList");
        if (!container) return;

        const upcomingEvents = filteredAcademicEvents
            .filter(event => ["upcoming", "ongoing"].includes(normalize(event.status)))
            .sort((first, second) => String(first.start_date).localeCompare(String(second.start_date)))
            .slice(0, 6);

        if (upcomingEvents.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center py-4">
                    <i class="fa-solid fa-calendar-xmark d-block mb-2" style="font-size:28px;"></i>
                    No upcoming events found.
                </div>
            `;
            return;
        }

        container.innerHTML = upcomingEvents.map(function (event) {
            const eventType = normalize(event.event_type) || "event";
            const color = getEventColor(eventType);
            return `
                <div class="upcoming-event" data-event-id="${Number(event.id)}" style="border-left-color:${color};">
                    <h6>${escapeHtml(event.title || "Untitled Event")}</h6>
                    <p>${escapeHtml(event.description || formatEventType(eventType))}</p>
                    <div class="event-date">
                        <i class="fa-solid fa-calendar me-1"></i>${escapeHtml(formatEventDateRange(event.start_date, event.end_date))}
                    </div>
                </div>
            `;
        }).join("");

        container.querySelectorAll(".upcoming-event").forEach(function (element) {
            element.addEventListener("click", function () {
                const eventId = Number(this.dataset.eventId);
                const event = findAcademicEvent(eventId);
                if (event?.start_date) academicCalendar?.gotoDate(event.start_date);
                openEventDetailsModal(eventId);
            });
        });
    }

    function bindAddEventControls() {
        document.getElementById("openAddEventBtn")?.addEventListener("click", function () {
            openAddEventModal();
        });

        document.getElementById("saveNewEventBtn")?.addEventListener("click", createHodAcademicEvent);

        document.getElementById("eventStartDate")?.addEventListener("change", function () {
            const endInput = document.getElementById("eventEndDate");
            if (endInput && !endInput.value) endInput.value = this.value;
        });
    }

    function openAddEventModal(selectedDate = "") {
        resetAddEventForm();
        setInputValue("eventDepartment", currentDepartment);

        if (selectedDate) {
            setInputValue("eventStartDate", selectedDate);
            setInputValue("eventEndDate", selectedDate);
        }

        bootstrap.Modal.getOrCreateInstance(document.getElementById("addEventModal")).show();
    }

    async function createHodAcademicEvent() {
        const form = document.getElementById("addEventForm");
        if (!form?.checkValidity()) {
            form?.reportValidity();
            return;
        }

        const payload = {
            title: document.getElementById("eventTitle")?.value.trim() || "",
            event_type: document.getElementById("eventType")?.value || "event",
            start_date: document.getElementById("eventStartDate")?.value || "",
            end_date: document.getElementById("eventEndDate")?.value || "",
            description: document.getElementById("eventDescription")?.value.trim() || ""
        };

        if (payload.end_date && payload.end_date < payload.start_date) {
            showCalendarMessage("End date cannot be before start date.", true);
            return;
        }

        const button = document.getElementById("saveNewEventBtn");
        setButtonLoading(button, true, "Adding...");

        try {
            const response = await API.request("POST", "/academic-events/hod", payload);

            if (!response || response.success !== true) {
                throw new Error(response?.message || "Unable to create academic event.");
            }

            bootstrap.Modal.getInstance(document.getElementById("addEventModal"))?.hide();
            resetAddEventForm();
            showCalendarMessage(response.message || "Academic event created successfully.");
            await loadHodAcademicEvents();
        }
        catch (error) {
            console.error("HOD Academic Event Create Error:", error);
            showCalendarMessage(error.message || "Unable to create academic event.", true);
        }
        finally {
            setButtonLoading(button, false);
        }
    }

    function resetAddEventForm() {
        document.getElementById("addEventForm")?.reset();
        setInputValue("eventDepartment", currentDepartment);
    }

    function bindEventActionControls() {
        document.getElementById("editEventBtn")?.addEventListener("click", function () {
            const event = findAcademicEvent(selectedAcademicEventId);
            if (!event || event.can_edit !== true) return;

            bootstrap.Modal.getInstance(document.getElementById("eventDetailsModal"))?.hide();
            window.setTimeout(() => openEditEventModal(event.id), 180);
        });

        document.getElementById("deleteEventBtn")?.addEventListener("click", function () {
            const event = findAcademicEvent(selectedAcademicEventId);
            if (!event || event.can_delete !== true) return;

            bootstrap.Modal.getInstance(document.getElementById("eventDetailsModal"))?.hide();
            window.setTimeout(() => openDeleteEventModal(event.id), 180);
        });

        document.getElementById("saveEventChangesBtn")?.addEventListener("click", updateHodAcademicEvent);
        document.getElementById("confirmDeleteEventBtn")?.addEventListener("click", deleteHodAcademicEvent);
    }

    function openEventDetailsModal(eventId) {
        const event = findAcademicEvent(eventId);
        if (!event) return;

        selectedAcademicEventId = Number(event.id);
        setText("detailsEventTitle", event.title || "Untitled Event");
        setText("detailsEventType", formatEventType(event.event_type));
        setText("detailsEventDate", formatEventDateRange(event.start_date, event.end_date));
        setText("detailsEventDepartment", event.department || "All Departments");
        setText("detailsEventScope", formatLabel(event.scope || "global"));
        setText("detailsEventDescription", event.description || "No description available.");

        const status = safeEventStatus(event.status);
        const statusElement = document.getElementById("detailsEventStatus");
        if (statusElement) {
            statusElement.className = `event-status ${status}`;
            statusElement.textContent = formatLabel(status);
        }

        const editButton = document.getElementById("editEventBtn");
        const deleteButton = document.getElementById("deleteEventBtn");
        if (editButton) editButton.style.display = event.can_edit === true ? "inline-block" : "none";
        if (deleteButton) deleteButton.style.display = event.can_delete === true ? "inline-block" : "none";

        bootstrap.Modal.getOrCreateInstance(document.getElementById("eventDetailsModal")).show();
    }

    function openEditEventModal(eventId) {
        const event = findAcademicEvent(eventId);
        if (!event || event.can_edit !== true) {
            showCalendarMessage("You can edit only events created by you.", true);
            return;
        }

        selectedAcademicEventId = Number(event.id);
        ensureSelectOption("editEventType", normalize(event.event_type), formatEventType(event.event_type));
        setInputValue("editEventId", event.id);
        setInputValue("editEventTitle", event.title || "");
        setInputValue("editEventType", normalize(event.event_type) || "event");
        setInputValue("editEventStartDate", toDateInputValue(event.start_date));
        setInputValue("editEventEndDate", toDateInputValue(event.end_date));
        setInputValue("editEventDescription", event.description || "");

        bootstrap.Modal.getOrCreateInstance(document.getElementById("editEventModal")).show();
    }

    async function updateHodAcademicEvent() {
        const form = document.getElementById("editEventForm");
        if (!selectedAcademicEventId || !form?.checkValidity()) {
            form?.reportValidity();
            return;
        }

        const payload = {
            title: document.getElementById("editEventTitle")?.value.trim() || "",
            event_type: document.getElementById("editEventType")?.value || "event",
            start_date: document.getElementById("editEventStartDate")?.value || "",
            end_date: document.getElementById("editEventEndDate")?.value || "",
            description: document.getElementById("editEventDescription")?.value.trim() || ""
        };

        if (payload.end_date && payload.end_date < payload.start_date) {
            showCalendarMessage("End date cannot be before start date.", true);
            return;
        }

        const button = document.getElementById("saveEventChangesBtn");
        setButtonLoading(button, true, "Saving...");

        try {
            const response = await API.request(
                "PATCH",
                `/academic-events/hod/${selectedAcademicEventId}`,
                payload
            );

            if (!response || response.success !== true) {
                throw new Error(response?.message || "Unable to update academic event.");
            }

            bootstrap.Modal.getInstance(document.getElementById("editEventModal"))?.hide();
            selectedAcademicEventId = null;
            showCalendarMessage(response.message || "Academic event updated successfully.");
            await loadHodAcademicEvents();
        }
        catch (error) {
            console.error("HOD Academic Event Update Error:", error);
            showCalendarMessage(error.message || "Unable to update academic event.", true);
        }
        finally {
            setButtonLoading(button, false);
        }
    }

    function openDeleteEventModal(eventId) {
        const event = findAcademicEvent(eventId);
        if (!event || event.can_delete !== true) {
            showCalendarMessage("You can delete only events created by you.", true);
            return;
        }

        selectedAcademicEventId = Number(event.id);
        setText("deleteEventTitle", event.title || "this event");
        bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteEventModal")).show();
    }

    async function deleteHodAcademicEvent() {
        if (!selectedAcademicEventId) return;

        const button = document.getElementById("confirmDeleteEventBtn");
        setButtonLoading(button, true, "Deleting...");

        try {
            const response = await API.request(
                "DELETE",
                `/academic-events/hod/${selectedAcademicEventId}`
            );

            if (!response || response.success !== true) {
                throw new Error(response?.message || "Unable to delete academic event.");
            }

            bootstrap.Modal.getInstance(document.getElementById("deleteEventModal"))?.hide();
            selectedAcademicEventId = null;
            showCalendarMessage(response.message || "Academic event deleted successfully.");
            await loadHodAcademicEvents();
        }
        catch (error) {
            console.error("HOD Academic Event Delete Error:", error);
            showCalendarMessage(error.message || "Unable to delete academic event.", true);
        }
        finally {
            setButtonLoading(button, false);
        }
    }

    function bindCalendarPageControls() {
        document.getElementById("todayCalendarBtn")?.addEventListener("click", function () {
            academicCalendar?.today();
        });
    }

    async function loadCalendarNotificationPreview() {
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
                        <li><a class="dropdown-item ${notification.is_read ? "" : "fw-semibold"}" href="notification.html">
                            <i class="fa-solid fa-bell me-2"></i>${escapeHtml(notification.title || "Notification")}
                        </a></li>
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

    function findAcademicEvent(eventId) {
        return hodAcademicEvents.find(event => Number(event.id) === Number(eventId));
    }

    function inclusiveEndToExclusive(endDate) {
        if (!endDate) return null;

        const match = String(endDate).match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (!match) return null;

        const date = new Date(Date.UTC(
            Number(match[1]),
            Number(match[2]) - 1,
            Number(match[3]) + 1
        ));
        return date.toISOString().slice(0, 10);
    }

    function getEventColor(eventType) {
        const colors = {
            academic: "#6d4aff",
            exam: "#dc2626",
            examination: "#dc2626",
            meeting: "#0891b2",
            holiday: "#16a34a",
            deadline: "#d97706",
            event: "#2563eb",
            placement: "#7c3aed",
            workshop: "#db2777"
        };
        return colors[normalize(eventType)] || "#64748b";
    }

    function formatEventType(value) {
        const normalized = normalize(value) || "event";
        if (normalized === "exam") return "Examination";
        return formatLabel(normalized);
    }

    function safeEventStatus(value) {
        const normalized = normalize(value);
        return ["upcoming", "ongoing", "completed"].includes(normalized)
            ? normalized
            : "upcoming";
    }

    function formatEventDateRange(startDate, endDate) {
        const start = formatDate(startDate);
        const end = formatDate(endDate);
        if (!endDate || String(startDate) === String(endDate)) return start;
        return `${start} - ${end}`;
    }

    function formatDate(value) {
        if (!value) return "--";

        const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
        if (!match) return String(value);

        const date = new Date(
            Number(match[1]),
            Number(match[2]) - 1,
            Number(match[3])
        );

        return date.toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric"
        });
    }

    function toDateInputValue(value) {
        if (!value) return "";
        const match = String(value).match(/^(\d{4}-\d{2}-\d{2})/);
        return match ? match[1] : "";
    }

    function ensureSelectOption(selectId, value, label) {
        const select = document.getElementById(selectId);
        if (!select || !value) return;

        const exists = [...select.options].some(option => option.value === value);
        if (!exists) {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = label || formatEventType(value);
            select.appendChild(option);
        }
    }

    function showCalendarFallback(message, isError = false) {
        const container = document.getElementById("academicCalendar");
        if (!container) return;
        container.innerHTML = `<div class="text-center py-5 ${isError ? "text-danger" : "text-muted"}">${escapeHtml(message)}</div>`;
    }

    function showCalendarMessage(message, isError = false) {
        const element = document.getElementById("calendarPageMessage");
        if (!element) return;

        window.clearTimeout(calendarMessageTimer);
        element.className = `alert calendar-message ${isError ? "alert-danger" : "alert-success"}`;
        element.textContent = String(message || "");
        element.style.display = "block";
        element.scrollIntoView({ behavior: "smooth", block: "nearest" });

        calendarMessageTimer = window.setTimeout(function () {
            element.style.display = "none";
        }, 5000);
    }

    function setCalendarButtonsDisabled(disabled) {
        ["openAddEventBtn", "todayCalendarBtn", "saveNewEventBtn"].forEach(function (id) {
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