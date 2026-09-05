// ============================================================
// FMPS TEACHER DASHBOARD
// Replace: js/teacher-dashboard.js
// ============================================================

(function () {
    "use strict";

    const BACKEND_URL = "http://127.0.0.1:5000";
    const API_URL = BACKEND_URL + "/api";
    const TOKEN_KEY = "fmps_access_token";

    let attendanceChart = null;
    let performanceChart = null;
    let calendar = null;
    let dashboardData = null;

    document.addEventListener("DOMContentLoaded", init);

    function init() {
        setupTheme();
        setupClock();
        setupNavigation();
        setupQuickActions();
        setupSearch();
        setupLogout();
        setupRefresh();

        if (!localStorage.getItem(TOKEN_KEY)) {
            window.location.replace("teacher-login.html");
            return;
        }

        loadDashboard();
    }

    // ========================================================
    // DASHBOARD LOADING
    // ========================================================

    async function loadDashboard() {
        setLoading(true);
        hideError();
        clearDashboardData();

        try {
            const dashboardResult = await apiRequest(
                "GET",
                "/teachers/me/dashboard"
            );

            if (!dashboardResult.success || !dashboardResult.data) {
                throw new Error(
                    dashboardResult.message || "Dashboard data not found"
                );
            }

            const data = Object.assign({}, dashboardResult.data);

            const extraResults = await Promise.allSettled([
                apiRequest("GET", "/faculty-attendance/teacher/self"),
                apiRequest("GET", "/academic-events/teacher/me")
            ]);

            const attendanceResult = extraResults[0];
            const calendarResult = extraResults[1];

            if (
                attendanceResult.status === "fulfilled" &&
                attendanceResult.value.success &&
                attendanceResult.value.data
            ) {
                mergeLatestAttendance(data, attendanceResult.value.data);
            }
            else if (
                attendanceResult.status === "rejected" &&
                isAuthenticationError(attendanceResult.reason)
            ) {
                throw attendanceResult.reason;
            }

            if (
                calendarResult.status === "fulfilled" &&
                calendarResult.value.success
            ) {
                data.academic_events = extractArray(calendarResult.value);
            }
            else if (
                calendarResult.status === "rejected" &&
                isAuthenticationError(calendarResult.reason)
            ) {
                throw calendarResult.reason;
            }

            dashboardData = data;
            renderDashboard(data);
        }
        catch (error) {
            console.error("Teacher dashboard error:", error);

            if (isAuthenticationError(error)) {
                clearLogin();
                window.location.replace("teacher-login.html");
                return;
            }

            showError(
                error.message || "Unable to load teacher dashboard data."
            );
            renderEmptyCharts();
        }
        finally {
            setLoading(false);
        }
    }

    function mergeLatestAttendance(data, attendanceData) {
        data.teacher = Object.assign(
            {},
            data.teacher || {},
            attendanceData.teacher || {}
        );
        data.attendance_summary = attendanceData.summary || {};
        data.attendance_records = toArray(attendanceData.records);
        data.face_registered = Boolean(attendanceData.face_registered);

        const today = attendanceData.today || {};
        data.today_attendance = today.record || {
            status: today.marked ? "present" : "pending",
            date: today.date || null,
            remarks: today.marked
                ? "Attendance marked"
                : "Attendance is not marked yet"
        };
    }

    // ========================================================
    // API
    // Uses api.js when available so refresh-token logic remains active.
    // ========================================================

    async function apiRequest(method, path, body) {
        if (
            window.API &&
            typeof window.API.request === "function"
        ) {
            return window.API.request(method, path, body || null);
        }

        const token = localStorage.getItem(TOKEN_KEY);
        const headers = { Accept: "application/json" };

        if (token) {
            headers.Authorization = "Bearer " + token;
        }

        if (body !== undefined && body !== null) {
            headers["Content-Type"] = "application/json";
        }

        const response = await fetch(API_URL + path, {
            method: method,
            headers: headers,
            body: body !== undefined && body !== null
                ? JSON.stringify(body)
                : undefined
        });

        const result = await response.json().catch(function () {
            return {};
        });

        if (!response.ok) {
            const error = new Error(
                result.message || result.error || "Request failed"
            );
            error.status = response.status;
            throw error;
        }

        return result;
    }

    // ========================================================
    // RENDER
    // ========================================================

    function renderDashboard(data) {
        const schedule = getTodaySchedule(data);
        const attendance = data.attendance_summary || {};
        const stats = data.stats || {};

        renderProfile(data.teacher || {}, data.user || {});
        renderCurrentClass(data.current_class, schedule);
        renderStats(stats, attendance, data.performance || {}, schedule, data);
        renderSchedule(schedule);
        renderAttendance(attendance);
        renderPerformance(data.performance || {}, stats);
        renderNotifications(getNotifications(data), stats);
        renderActivities(data);
        renderCalendar(getAcademicEvents(data));
    }

    // ========================================================
    // PROFILE AND WELCOME
    // ========================================================

    function renderProfile(teacher, user) {
        const fullName =
            teacher.full_name ||
            teacher.name ||
            user.full_name ||
            user.username ||
            "Teacher";
        const designation =
            teacher.designation ||
            teacher.role ||
            "Faculty Member";
        const email = user.email || teacher.email || designation;
        const shortName = firstName(fullName);
        const fallbackPhoto = createInitialsAvatar(fullName);
        const photo = resolvePhotoUrl(
            teacher.photo_url || teacher.profile_photo || user.photo_url
        ) || fallbackPhoto;

        document
            .querySelectorAll(".profile-avatar, .profile-header img")
            .forEach(function (image) {
                image.src = photo;
                image.alt = fullName;
                image.onerror = function () {
                    this.onerror = null;
                    this.src = fallbackPhoto;
                };
            });

        changeText(".profile-copy strong", shortName);
        changeText(".profile-copy small", designation);
        changeText(".profile-header h5", fullName);
        changeText(".profile-header span", email);
        setText("dashboardGreeting", greetingText(shortName));
        setText("welcomeTitle", "Welcome Back, " + shortName + " 👋");
    }

    function greetingText(name) {
        const hour = new Date().getHours();
        const greeting = hour < 12
            ? "Good Morning"
            : hour < 17
                ? "Good Afternoon"
                : "Good Evening";

        return greeting + ", " + name;
    }

    // ========================================================
    // CURRENT CLASS AND SCHEDULE
    // ========================================================

    function getTodaySchedule(data) {
        const candidates = [
            data.today_schedule,
            data.schedule,
            data.timetable && data.timetable.schedule,
            data.timetable && data.timetable.today_schedule
        ];

        for (const candidate of candidates) {
            if (Array.isArray(candidate)) {
                return candidate;
            }
        }

        return [];
    }

    function renderCurrentClass(currentClass, schedule) {
        const card = document.getElementById("currentClassCard");
        let selected = currentClass || findCurrentOrNextClass(schedule);
        let label = selected && selected.__isNext
            ? "NEXT CLASS"
            : "CURRENT CLASS";

        if (!card) {
            return;
        }

        if (!selected) {
            card.classList.add("is-empty");
            setText("currentClassLabel", "TODAY'S STATUS");
            setText("currentClassSubject", "No class right now");
            setText(
                "currentClassDetails",
                schedule.length
                    ? "Today's scheduled classes are complete"
                    : "No classes scheduled for today"
            );
            return;
        }

        card.classList.remove("is-empty");
        setText("currentClassLabel", label);
        setText(
            "currentClassSubject",
            selected.subject ||
            selected.subject_name ||
            selected.course_name ||
            "Scheduled Class"
        );

        const time = formatTime(selected.start_time) +
            (selected.end_time
                ? " – " + formatTime(selected.end_time)
                : "");
        const room = selected.room || selected.room_number || selected.venue;

        setText(
            "currentClassDetails",
            [time, room].filter(Boolean).join(" · ") || "Class details unavailable"
        );
    }

    function findCurrentOrNextClass(schedule) {
        if (!schedule.length) {
            return null;
        }

        const now = new Date();
        const currentMinutes = now.getHours() * 60 + now.getMinutes();
        let nextClass = null;

        for (const item of schedule) {
            const start = timeToMinutes(item.start_time);
            const end = timeToMinutes(item.end_time);

            if (start === null) {
                continue;
            }

            if (currentMinutes >= start && (end === null || currentMinutes <= end)) {
                return item;
            }

            if (start > currentMinutes && (!nextClass || start < nextClass.start)) {
                nextClass = { item: item, start: start };
            }
        }

        if (!nextClass) {
            return null;
        }

        return Object.assign({}, nextClass.item, { __isNext: true });
    }

    function renderSchedule(schedule) {
        const body = document.getElementById("todayScheduleBody");

        if (!body) {
            return;
        }

        body.replaceChildren();

        if (!schedule.length) {
            showTableMessage(body, "No classes scheduled for today.");
            return;
        }

        schedule.forEach(function (entry) {
            const row = document.createElement("tr");
            const subject =
                entry.subject ||
                entry.subject_name ||
                entry.course_name ||
                "Not specified";
            const room =
                entry.room ||
                entry.room_number ||
                entry.venue ||
                "Not specified";

            addCell(
                row,
                formatTime(entry.start_time) +
                (entry.end_time ? " – " + formatTime(entry.end_time) : "")
            );
            addCell(row, subject);
            addCell(row, room);
            body.appendChild(row);
        });
    }

    function showTableMessage(body, message) {
        body.replaceChildren();
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 3;
        cell.className = "empty-state";
        cell.textContent = message;
        row.appendChild(cell);
        body.appendChild(row);
    }

    // ========================================================
    // STATS
    // ========================================================

    function renderStats(stats, attendance, performance, schedule, data) {
        const cards = document.querySelectorAll(".dashboard-cards .card-box");
        const attendancePercentage = firstNumber([
            attendance.attendance_percentage,
            attendance.percentage,
            stats.attendance_percentage
        ]);
        const pendingLeaves = firstNumber([
            stats.pending_leave_requests,
            stats.pending_leaves,
            countPendingLeaves(data.recent_leaves)
        ]);
        const performancePercentage = firstNumber([
            stats.performance_percentage,
            performance.attendance_percentage,
            performance.average_percentage,
            performance.percentage,
            calculatePerformanceAverage(performance)
        ]);
        const classCount = firstNumber([
            stats.today_classes,
            stats.total_classes_today,
            schedule.length
        ]);

        setCard(cards[0], classCount, "Today's Classes", "Scheduled today");
        setCard(cards[1], attendancePercentage, "Attendance", "Overall percentage", "%");
        setCard(cards[2], pendingLeaves, "Pending Leave Requests", "Awaiting HOD decision");
        setCard(cards[3], performancePercentage, "Performance", "Latest overall score", "%");
    }

    function setCard(card, value, label, helper, suffix) {
        if (!card) {
            return;
        }

        const number = card.querySelector("h3");
        const title = card.querySelector("p");
        const description = card.querySelector("div:last-child > span");

        if (title) {
            title.textContent = label;
        }

        if (description) {
            description.textContent = helper;
        }

        if (!number) {
            return;
        }

        if (value === null || value === undefined || value === "") {
            number.textContent = "N/A";
            return;
        }

        const numeric = Number(value);
        number.textContent = Number.isFinite(numeric)
            ? formatNumber(numeric) + (suffix || "")
            : String(value);
    }

    // ========================================================
    // ATTENDANCE CHART
    // ========================================================

    function renderAttendance(summary) {
        const element = document.getElementById("attendanceChart");
        const present = Number(summary.present || 0);
        const absent = Number(summary.absent || 0);
        const leave = Number(summary.leave || 0);
        const total = present + absent + leave;
        const percentage = firstNumber([
            summary.attendance_percentage,
            summary.percentage,
            total > 0 ? (present / total) * 100 : 0
        ]);

        setText(
            "attendanceCenterValue",
            percentage === null ? "--" : formatNumber(percentage) + "%"
        );

        if (!element || typeof Chart === "undefined") {
            return;
        }

        if (attendanceChart) {
            attendanceChart.destroy();
        }

        const hasData = total > 0;

        attendanceChart = new Chart(element, {
            type: "doughnut",
            data: {
                labels: hasData
                    ? ["Present", "Absent", "Leave"]
                    : ["No attendance records"],
                datasets: [{
                    data: hasData ? [present, absent, leave] : [1],
                    backgroundColor: hasData
                        ? ["#7352ff", "#ff5f6d", "#ffb44b"]
                        : [gridColor()],
                    borderWidth: 0,
                    hoverOffset: hasData ? 5 : 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "72%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: textColor(),
                            usePointStyle: true,
                            boxWidth: 8,
                            padding: 16,
                            font: { family: "Poppins", size: 10 }
                        }
                    },
                    tooltip: { enabled: hasData }
                }
            }
        });
    }

    // ========================================================
    // PERFORMANCE CHART
    // ========================================================

    function renderPerformance(performance, stats) {
        const element = document.getElementById("performanceChart");
        const empty = document.getElementById("performanceEmpty");
        const records = Array.isArray(performance)
            ? performance.slice()
            : toArray(performance.records).slice();
        let labels = records.map(function (record) {
            return record.term ||
                record.subject ||
                record.subject_name ||
                record.review_period ||
                "Record";
        });
        let values = records.map(calculateRecordPercentage);

        if (!records.length) {
            const overall = firstNumber([
                stats.performance_percentage,
                performance.average_percentage,
                performance.percentage
            ]);

            if (overall !== null) {
                labels = ["Current Performance"];
                values = [overall];
            }
        }

        if (empty) {
            empty.hidden = values.length > 0;
        }

        if (!element || typeof Chart === "undefined") {
            return;
        }

        if (performanceChart) {
            performanceChart.destroy();
            performanceChart = null;
        }

        if (!values.length) {
            element.hidden = true;
            return;
        }

        element.hidden = false;
        performanceChart = new Chart(element, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Performance %",
                    data: values,
                    borderColor: "#7b5cff",
                    backgroundColor: "rgba(123, 92, 255, .15)",
                    pointBackgroundColor: "#ffffff",
                    pointBorderColor: "#7b5cff",
                    pointBorderWidth: 3,
                    pointRadius: 4,
                    fill: true,
                    tension: .35
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        suggestedMax: 100,
                        ticks: { color: textColor(), font: chartFont() },
                        grid: { color: gridColor() }
                    },
                    x: {
                        ticks: { color: textColor(), font: chartFont() },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: textColor(),
                            usePointStyle: true,
                            font: chartFont()
                        }
                    }
                }
            }
        });
    }

    function calculateRecordPercentage(record) {
        const direct = firstNumber([
            record.percentage,
            record.performance_percentage,
            record.overall_percentage
        ]);

        if (direct !== null) {
            return Number(direct.toFixed(1));
        }

        const score = firstNumber([
            record.score,
            record.total_score,
            record.marks_obtained
        ]) || 0;
        const maximum = firstNumber([
            record.max_score,
            record.maximum_score,
            record.total_marks
        ]) || 0;

        return maximum > 0
            ? Number(((score / maximum) * 100).toFixed(1))
            : 0;
    }

    function calculatePerformanceAverage(performance) {
        const records = Array.isArray(performance)
            ? performance
            : toArray(performance.records);

        if (!records.length) {
            return null;
        }

        const values = records
            .map(calculateRecordPercentage)
            .filter(Number.isFinite);

        if (!values.length) {
            return null;
        }

        return values.reduce(function (sum, value) {
            return sum + value;
        }, 0) / values.length;
    }

    function renderEmptyCharts() {
        renderAttendance({});
        renderPerformance({}, {});
    }

    function updateChartColors() {
        [attendanceChart, performanceChart].forEach(function (chart) {
            if (!chart) {
                return;
            }

            if (
                chart.options.plugins &&
                chart.options.plugins.legend &&
                chart.options.plugins.legend.labels
            ) {
                chart.options.plugins.legend.labels.color = textColor();
            }

            if (chart.options.scales) {
                Object.values(chart.options.scales).forEach(function (scale) {
                    if (scale.ticks) {
                        scale.ticks.color = textColor();
                    }
                    if (scale.grid) {
                        scale.grid.color = gridColor();
                    }
                });
            }

            chart.update();
        });
    }

    // ========================================================
    // NOTIFICATIONS AND ACTIVITIES
    // ========================================================

    function getNotifications(data) {
        const candidates = [
            data.notifications,
            data.recent_notifications,
            data.notification_data
        ];

        for (const candidate of candidates) {
            if (Array.isArray(candidate)) {
                return candidate;
            }
        }

        return [];
    }

    function renderNotifications(notifications, stats) {
        const unread = firstNumber([
            stats.unread_notifications,
            notifications.filter(function (item) {
                return !item.is_read;
            }).length
        ]) || 0;

        updateNotificationCount(unread);

        const menu = document.querySelector(".notification-menu");

        if (menu) {
            menu.replaceChildren();
            menu.appendChild(createNotificationHeader(notifications, stats));

            if (!notifications.length) {
                const item = document.createElement("li");
                const text = document.createElement("span");
                text.className = "dropdown-item-text text-muted";
                text.textContent = "No notifications available.";
                item.appendChild(text);
                menu.appendChild(item);
            }

            notifications.slice(0, 6).forEach(function (notification) {
                menu.appendChild(
                    createNotificationItem(notification, notifications, stats)
                );
            });
        }

        fillList(
            document.getElementById("dashboardNotifications"),
            notifications.slice(0, 5).map(function (item) {
                return {
                    icon: notificationIcon(item),
                    text: item.title || item.message || "Notification",
                    detail: item.title && item.message ? item.message : "",
                    date: item.created_at
                };
            }),
            "No notifications available."
        );
    }

    function createNotificationHeader(notifications, stats) {
        const header = document.createElement("li");
        const heading = document.createElement("span");
        const button = document.createElement("button");
        const unread = notifications.filter(function (item) {
            return !item.is_read;
        }).length;

        header.className = "dropdown-header d-flex justify-content-between align-items-center";
        heading.textContent = "Notifications";
        button.type = "button";
        button.className = "btn btn-sm btn-link text-decoration-none p-0";
        button.textContent = "Mark all read";
        button.disabled = unread === 0;

        button.addEventListener("click", async function (event) {
            event.stopPropagation();
            button.disabled = true;

            try {
                await apiRequest("PATCH", "/notifications/read-all");
                notifications.forEach(function (notification) {
                    notification.is_read = true;
                });
                stats.unread_notifications = 0;
                renderNotifications(notifications, stats);
            }
            catch (error) {
                button.disabled = false;
                showError(error.message || "Unable to update notifications.");
            }
        });

        header.append(heading, button);
        return header;
    }

    function createNotificationItem(notification, notifications, stats) {
        const item = document.createElement("li");
        const link = document.createElement("a");
        const title = document.createElement("strong");
        const message = document.createElement("small");

        link.className = "dropdown-item notification-item";
        link.href = notification.link || "#";
        title.textContent = notification.title || "Notification";
        message.textContent = notification.message || "";
        link.append(title, message);

        if (notification.is_read) {
            link.style.opacity = ".62";
        }

        link.addEventListener("click", async function (event) {
            const target = notification.link;

            if (!notification.is_read && notification.id) {
                event.preventDefault();

                try {
                    await apiRequest(
                        "PATCH",
                        "/notifications/" + notification.id + "/read"
                    );
                    notification.is_read = true;
                    stats.unread_notifications = Math.max(
                        0,
                        Number(stats.unread_notifications || 1) - 1
                    );
                    renderNotifications(notifications, stats);
                }
                catch (error) {
                    console.error("Notification update error:", error);
                }
            }

            if (target && target !== "#") {
                window.location.href = target;
            }
            else {
                event.preventDefault();
            }
        });

        item.appendChild(link);
        return item;
    }

    function updateNotificationCount(value) {
        const count = document.getElementById("notificationCount");

        if (!count) {
            return;
        }

        const unread = Math.max(0, Number(value || 0));
        count.textContent = unread > 99 ? "99+" : String(unread);
        count.style.display = unread > 0 ? "inline-flex" : "none";
    }

    function renderActivities(data) {
        const items = [];
        const attendance = data.today_attendance || {};

        if (attendance.status && attendance.status !== "pending") {
            items.push({
                icon: attendance.status === "holiday"
                    ? "fa-calendar-day"
                    : "fa-user-check",
                text: attendance.status === "holiday"
                    ? "Today is a non-working day"
                    : "Today's attendance: " + titleCase(attendance.status),
                detail: attendance.remarks || "",
                date: attendance.updated_at || attendance.created_at || attendance.date
            });
        }

        toArray(data.recent_leaves).forEach(function (leave) {
            items.push({
                icon: "fa-file-circle-check",
                text: "Leave request: " + titleCase(leave.status),
                detail: leave.leave_type || leave.reason || "",
                date: leave.updated_at || leave.created_at
            });
        });

        getNotifications(data).forEach(function (notification) {
            items.push({
                icon: notificationIcon(notification),
                text: notification.title || "Notification",
                detail: notification.message || "",
                date: notification.created_at
            });
        });

        items.sort(function (first, second) {
            return safeDateValue(second.date) - safeDateValue(first.date);
        });

        fillList(
            document.getElementById("recentActivities"),
            items.slice(0, 5),
            "No recent activity available."
        );
    }

    function fillList(list, items, emptyText) {
        if (!list) {
            return;
        }

        list.replaceChildren();
        const finalItems = items.length
            ? items
            : [{ icon: "fa-circle-info", text: emptyText }];

        finalItems.forEach(function (item) {
            const row = document.createElement("li");
            const icon = document.createElement("i");
            const copy = document.createElement("span");
            const text = document.createElement("strong");

            icon.className = "fa-solid " + (item.icon || "fa-circle-info");
            text.textContent = item.text || "Update";
            copy.appendChild(text);

            if (item.detail) {
                const detail = document.createElement("small");
                detail.textContent = item.detail;
                copy.appendChild(detail);
            }

            row.append(icon, copy);
            list.appendChild(row);
        });
    }

    function notificationIcon(notification) {
        const type = String(
            notification.type || notification.notification_type || ""
        ).toLowerCase();

        if (type.includes("leave")) {
            return "fa-file-circle-check";
        }
        if (type.includes("notice")) {
            return "fa-bullhorn";
        }
        if (type.includes("attendance")) {
            return "fa-user-check";
        }
        return "fa-bell";
    }

    // ========================================================
    // ACADEMIC CALENDAR
    // ========================================================

    function getAcademicEvents(data) {
        const candidates = [
            data.academic_events,
            data.events,
            data.calendar_events
        ];

        for (const candidate of candidates) {
            if (Array.isArray(candidate)) {
                return candidate;
            }
        }

        return [];
    }

    function renderCalendar(events) {
        const element = document.getElementById("calendar");
        const status = document.getElementById("calendarStatus");

        if (!element) {
            return;
        }

        if (typeof FullCalendar === "undefined") {
            if (status) {
                status.textContent = "Calendar library could not load.";
            }
            return;
        }

        if (status) {
            status.textContent = events.length
                ? events.length + " academic event(s) loaded."
                : "No academic events are currently available.";
        }

        if (calendar) {
            calendar.destroy();
        }

        calendar = new FullCalendar.Calendar(element, {
            initialView: "dayGridMonth",
            height: "auto",
            headerToolbar: {
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth,listMonth"
            },
            dayMaxEvents: true,
            events: events.map(function (event) {
                return {
                    title: event.title || event.name || "Academic Event",
                    start: event.start_date || event.start,
                    end: event.end_date
                        ? nextDate(event.end_date)
                        : event.end,
                    color: calendarEventColor(event),
                    extendedProps: {
                        type: event.event_type,
                        scope: event.scope
                    }
                };
            })
        });

        calendar.render();
    }

    function calendarEventColor(event) {
        const type = String(event.event_type || event.type || "").toLowerCase();

        if (type.includes("holiday")) {
            return "#ef5f6c";
        }
        if (type.includes("exam")) {
            return "#f39c45";
        }
        return "#6f4cf5";
    }

    // ========================================================
    // UI SETUP
    // ========================================================

    function setupTheme() {
        const savedTheme = localStorage.getItem("theme") || "dark";
        document.body.classList.toggle("dark", savedTheme === "dark");
        updateThemeButtons();

        const button = document.getElementById("themeToggle");
        const menu = document.getElementById("themeMenu");

        if (button) {
            button.addEventListener("click", toggleTheme);
        }

        if (menu) {
            menu.addEventListener("click", toggleTheme);
        }
    }

    function toggleTheme() {
        document.body.classList.toggle("dark");
        localStorage.setItem(
            "theme",
            document.body.classList.contains("dark") ? "dark" : "light"
        );
        updateThemeButtons();
        updateChartColors();

        if (calendar && dashboardData) {
            renderCalendar(getAcademicEvents(dashboardData));
        }
    }

    function updateThemeButtons() {
        const dark = document.body.classList.contains("dark");
        const button = document.getElementById("themeToggle");
        const menu = document.getElementById("themeMenu");

        if (button) {
            button.innerHTML = dark
                ? '<i class="fa-solid fa-sun"></i>'
                : '<i class="fa-solid fa-moon"></i>';
        }

        if (menu) {
            menu.innerHTML = dark
                ? '<i class="fa-solid fa-sun"></i> Light Mode'
                : '<i class="fa-solid fa-moon"></i> Dark Mode';
        }
    }

    function setupClock() {
        updateClock();
        window.setInterval(updateClock, 1000);
    }

    function updateClock() {
        const now = new Date();
        setText(
            "liveTime",
            now.toLocaleTimeString("en-IN", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            })
        );
        setText(
            "liveDay",
            now.toLocaleDateString("en-IN", { weekday: "long" })
        );
        setText(
            "liveDate",
            now.toLocaleDateString("en-IN", {
                day: "numeric",
                month: "long",
                year: "numeric"
            })
        );
    }

    function setupNavigation() {
        const toggle = document.getElementById("sidebarToggle");
        const overlay = document.getElementById("sidebarOverlay");

        if (toggle) {
            toggle.addEventListener("click", function () {
                document.body.classList.toggle("sidebar-open");
            });
        }

        if (overlay) {
            overlay.addEventListener("click", closeSidebar);
        }

        const currentPage = window.location.pathname.split("/").pop();

        document.querySelectorAll(".sidebar-menu a[href]").forEach(function (link) {
            const page = link.getAttribute("href").split("?")[0].split("/").pop();
            const item = link.closest("li");

            if (item && page === currentPage) {
                document.querySelectorAll(".sidebar-menu li.active")
                    .forEach(function (active) {
                        active.classList.remove("active");
                    });
                item.classList.add("active");
            }

            link.addEventListener("click", closeSidebar);
        });
    }

    function closeSidebar() {
        document.body.classList.remove("sidebar-open");
    }

    function setupQuickActions() {
        const actions = {
            quickTakeAttendance: "face-attendance.html",
            quickUploadNotes: "face-register.html",
            quickAddAssignment: "leave-request.html",
            quickViewReports: "notices.html"
        };

        Object.keys(actions).forEach(function (id) {
            const button = document.getElementById(id);

            if (button) {
                button.addEventListener("click", function () {
                    window.location.href = actions[id];
                });
            }
        });
    }

    function setupSearch() {
        const search = document.getElementById("searchBox");

        if (!search) {
            return;
        }

        search.addEventListener("input", function () {
            const value = this.value.trim().toLowerCase();

            document.querySelectorAll(".searchable-section")
                .forEach(function (section) {
                    section.hidden = Boolean(
                        value && !section.innerText.toLowerCase().includes(value)
                    );
                });
        });
    }

    function setupLogout() {
        document.querySelectorAll('a[href="teacher-login.html"]')
            .forEach(function (link) {
                link.addEventListener("click", function (event) {
                    event.preventDefault();
                    clearLogin();
                    window.location.replace("teacher-login.html");
                });
            });
    }

    function setupRefresh() {
        const button = document.getElementById("refreshDashboardBtn");

        if (button) {
            button.addEventListener("click", loadDashboard);
        }
    }

    function clearLogin() {
        localStorage.removeItem("fmps_access_token");
        localStorage.removeItem("fmps_refresh_token");
        localStorage.removeItem("fmps_user");
    }

    function setLoading(loading) {
        const button = document.getElementById("refreshDashboardBtn");

        if (!button) {
            return;
        }

        button.disabled = loading;
        const icon = button.querySelector("i");

        if (icon) {
            icon.classList.toggle("fa-spin", loading);
        }
    }

    function clearDashboardData() {
        document.querySelectorAll(".dashboard-cards h3").forEach(function (item) {
            item.textContent = "--";
        });

        const scheduleBody = document.getElementById("todayScheduleBody");
        if (scheduleBody) {
            showTableMessage(scheduleBody, "Loading today's schedule...");
        }

        fillList(
            document.getElementById("recentActivities"),
            [],
            "Loading recent activity..."
        );
        fillList(
            document.getElementById("dashboardNotifications"),
            [],
            "Loading notifications..."
        );
        updateNotificationCount(0);
    }

    // ========================================================
    // HELPERS
    // ========================================================

    function setText(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    function changeText(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }

    function addCell(row, value) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
    }

    function extractArray(result) {
        if (Array.isArray(result)) {
            return result;
        }
        if (result && Array.isArray(result.data)) {
            return result.data;
        }
        if (result && result.data && Array.isArray(result.data.events)) {
            return result.data.events;
        }
        return [];
    }

    function toArray(value) {
        return Array.isArray(value) ? value : [];
    }

    function firstName(value) {
        return String(value || "Teacher").trim().split(/\s+/)[0] || "Teacher";
    }

    function titleCase(value) {
        return String(value || "")
            .replace(/_/g, " ")
            .replace(/\b\w/g, function (letter) {
                return letter.toUpperCase();
            });
    }

    function firstNumber(values) {
        for (const value of values) {
            if (value === null || value === undefined || value === "") {
                continue;
            }

            const number = Number(value);
            if (Number.isFinite(number)) {
                return number;
            }
        }
        return null;
    }

    function formatNumber(value) {
        return Number.isInteger(value)
            ? String(value)
            : value.toFixed(1);
    }

    function countPendingLeaves(leaves) {
        if (!Array.isArray(leaves)) {
            return null;
        }

        return leaves.filter(function (leave) {
            return String(leave.status || "").toLowerCase() === "pending";
        }).length;
    }

    function safeDateValue(value) {
        const timestamp = value ? new Date(value).getTime() : 0;
        return Number.isFinite(timestamp) ? timestamp : 0;
    }

    function isAuthenticationError(error) {
        return error && (error.status === 401 || error.status === 403);
    }

    function textColor() {
        return document.body.classList.contains("dark")
            ? "#b9c2d4"
            : "#58657b";
    }

    function gridColor() {
        return document.body.classList.contains("dark")
            ? "rgba(174, 184, 202, .14)"
            : "rgba(72, 84, 108, .12)";
    }

    function chartFont() {
        return { family: "Poppins", size: 10 };
    }

    function resolvePhotoUrl(value) {
        const photo = String(value || "").trim().replace(/\\/g, "/");

        if (!photo) {
            return "";
        }

        if (/^(https?:|data:|blob:)/i.test(photo)) {
            return photo;
        }

        return photo.startsWith("/")
            ? BACKEND_URL + photo
            : BACKEND_URL + "/" + photo;
    }

    function createInitialsAvatar(name) {
        const initials = String(name || "Teacher")
            .trim()
            .split(/\s+/)
            .slice(0, 2)
            .map(function (part) {
                return part.charAt(0).toUpperCase();
            })
            .join("")
            .replace(/[^A-Z0-9]/g, "") || "T";
        const svg =
            '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120">' +
            '<rect width="120" height="120" rx="60" fill="#6f42f5"/>' +
            '<text x="60" y="67" text-anchor="middle" font-family="Arial,sans-serif" ' +
            'font-size="42" font-weight="700" fill="#fff">' +
            initials +
            "</text></svg>";

        return "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg);
    }

    function nextDate(value) {
        const parts = String(value).slice(0, 10).split("-").map(Number);

        if (parts.length !== 3 || parts.some(function (part) {
            return !Number.isFinite(part);
        })) {
            return undefined;
        }

        return new Date(
            Date.UTC(parts[0], parts[1] - 1, parts[2] + 1)
        ).toISOString().slice(0, 10);
    }

    function timeToMinutes(value) {
        if (!value) {
            return null;
        }

        const parts = String(value).split(":");
        const hour = Number(parts[0]);
        const minute = Number(parts[1] || 0);

        return Number.isFinite(hour) && Number.isFinite(minute)
            ? hour * 60 + minute
            : null;
    }

    function formatTime(value) {
        if (!value) {
            return "--";
        }

        const parts = String(value).split(":");
        let hour = Number(parts[0]);
        const minute = parts[1] || "00";

        if (!Number.isFinite(hour)) {
            return String(value);
        }

        const period = hour >= 12 ? "PM" : "AM";
        hour = hour % 12 || 12;

        return String(hour).padStart(2, "0") + ":" + minute + " " + period;
    }

    function showError(message) {
        const alert = document.getElementById("teacherDashboardError");

        if (alert) {
            alert.hidden = false;
            alert.textContent = message || "Unable to load dashboard data.";
        }
    }

    function hideError() {
        const alert = document.getElementById("teacherDashboardError");

        if (alert) {
            alert.hidden = true;
            alert.textContent = "";
        }
    }

})();
