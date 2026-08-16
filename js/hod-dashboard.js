"use strict";


/* ============================================================
   GLOBAL DASHBOARD STATE
============================================================ */

window.currentHodDashboardData = null;
window.currentHodAnalyticsData = null;
window.currentHodNotifications = [];

let attendanceChartInstance = null;
let performanceChartInstance = null;
let teacherOverviewChartInstance = null;
let hodCalendarInstance = null;


/* ============================================================
   INITIALIZATION
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    async function () {

        const authenticated =
            await protectHodDashboard();

        if (!authenticated) {
            return;
        }

        /*
         * Remove visible dummy content immediately.
         * Real values will be loaded below.
         */
        prepareDashboardForRealData();

        setupClock();
        setupSearch();
        setupTheme();
        setupLogout();

        /*
         * Load basic dashboard + leave count first
         * because these are the top cards.
         */
        await loadHodDashboardData();
        await loadPendingLeaveRequests();

        setupCounters();

        /*
         * Remaining real dashboard sections.
         */
        await loadDashboardAnalytics();

        await loadTeacherPerformance();

        await loadTeacherOverview();

        await loadDashboardNotifications();

        await setupCalendar();

        setupExportData();
    }
);


/* ============================================================
   REMOVE / REPLACE HARDCODED DUMMY CONTENT
============================================================ */

function prepareDashboardForRealData() {

    /* ---------------- Notification badge ---------------- */

    const notificationCount =
        document.getElementById(
            "notificationCount"
        );

    if (notificationCount) {
        notificationCount.textContent = "0";
        notificationCount.style.display = "none";
    }


    /* ---------------- Profile dummy image ---------------- */

    const profileImage =
        document.querySelector(
            ".profile img"
        );

    if (profileImage) {
        profileImage.src =
            "../../images/logo.png";
    }


    /* ---------------- Teacher performance dummy rows ---------------- */

    const performanceTableBody =
        getTeacherPerformanceTableBody();

    if (performanceTableBody) {

        performanceTableBody.innerHTML = `
            <tr>
                <td
                    colspan="3"
                    class="text-center py-4 text-muted">
                    Loading performance records...
                </td>
            </tr>
        `;
    }


    /* ---------------- Recent activities dummy data ---------------- */

    const activityLists =
        document.querySelectorAll(
            ".activity-list"
        );

    if (activityLists.length > 0) {

        activityLists[0].innerHTML = `
            <li class="text-muted">
                Loading recent activities...
            </li>
        `;
    }


    /* ---------------- Bottom notifications dummy data ---------------- */

    if (activityLists.length > 1) {

        activityLists[1].innerHTML = `
            <li class="text-muted">
                Loading notifications...
            </li>
        `;
    }


    /* ---------------- Top notification dropdown ---------------- */

    const notificationMenu =
        document.querySelector(
            ".notification-menu"
        );

    if (notificationMenu) {

        notificationMenu.innerHTML = `
            <li class="dropdown-header">
                Notifications
            </li>

            <li>
                <div
                    class="dropdown-item text-muted text-center">
                    Loading notifications...
                </div>
            </li>

            <li>
                <hr class="dropdown-divider">
            </li>

            <li>
                <a
                    href="#"
                    class="dropdown-item text-center"
                    id="markAllRead">
                    Mark All as Read
                </a>
            </li>
        `;
    }
}


/* ============================================================
   AUTHENTICATION
============================================================ */

async function protectHodDashboard() {

    const token =
        localStorage.getItem(
            "fmps_access_token"
        );

    if (!token) {

        window.location.replace(
            "hod-login.html"
        );

        return false;
    }


    if (
        typeof API === "undefined" ||
        !API.auth
    ) {

        console.error(
            "FMPS API client is not loaded."
        );

        return false;
    }


    try {

        const response =
            await API.auth.me();


        console.log(
            "HOD Authentication:",
            response
        );


        let user = null;


        if (
            response &&
            response.data &&
            response.data.user
        ) {

            user =
                response.data.user;
        }

        else if (
            response &&
            response.data
        ) {

            user =
                response.data;
        }

        else if (
            response &&
            response.user
        ) {

            user =
                response.user;
        }

        else {

            user =
                response;
        }


        if (
            !user ||
            typeof user !== "object"
        ) {

            API.auth.logout();

            window.location.replace(
                "hod-login.html"
            );

            return false;
        }


        const role =
            String(
                user.role || ""
            )
                .trim()
                .toLowerCase();


        if (role !== "hod") {

            API.auth.logout();

            alert(
                "Access denied. HOD account required."
            );

            window.location.replace(
                "hod-login.html"
            );

            return false;
        }


        if (
            user.is_active === false ||
            user.is_active === 0
        ) {

            API.auth.logout();

            alert(
                "Your HOD account is inactive."
            );

            window.location.replace(
                "hod-login.html"
            );

            return false;
        }


        localStorage.setItem(
            "fmps_user",
            JSON.stringify(user)
        );


        displayAuthenticatedUser(
            user
        );


        return true;
    }

    catch (error) {

        console.error(
            "HOD Authentication Error:",
            error
        );


        if (
            typeof API !== "undefined" &&
            API.auth
        ) {

            API.auth.logout();
        }

        else {

            localStorage.removeItem(
                "fmps_access_token"
            );

            localStorage.removeItem(
                "fmps_user"
            );
        }


        window.location.replace(
            "hod-login.html"
        );


        return false;
    }
}


/* ============================================================
   BASIC AUTH USER DISPLAY
============================================================ */

function displayAuthenticatedUser(
    user
) {

    const name =
        user.username ||
        user.email ||
        "HOD";


    const profileName =
        document.querySelector(
            ".profile span"
        );


    if (profileName) {

        profileName.textContent =
            "Welcome, " + name;
    }


    const heading =
        document.getElementById(
            "hodWelcomeHeading"
        );


    if (heading) {

        heading.textContent =
            "Welcome Back, " +
            name +
            " 👋";
    }
}


/* ============================================================
   LOAD REAL HOD DASHBOARD
============================================================ */

async function loadHodDashboardData() {

    try {

        const response =
            await API.request(
                "GET",
                "/hods/dashboard"
            );


        console.log(
            "HOD Dashboard:",
            response
        );


        if (
            !response ||
            response.success !== true ||
            !response.data
        ) {

            throw new Error(
                response?.message ||
                "Unable to load HOD dashboard."
            );
        }


        const data =
            response.data;


        window.currentHodDashboardData =
            data;


        setCounterTarget(
            "hodTotalTeachers",
            data.total_teachers
        );


        setCounterTarget(
            "hodTotalStudents",
            data.total_students
        );


        setCounterTarget(
            "hodTotalDepartments",
            data.total_departments
        );


        /*
         * Pending leave count is loaded
         * from leave API separately.
         */
        setCounterTarget(
            "hodPendingRequests",
            0
        );


        /* ---------------- Real HOD profile ---------------- */

        if (data.hod) {

            displayRealHodProfile(
                data.hod
            );
        }


        /* ---------------- Department welcome text ---------------- */

        const description =
            document.getElementById(
                "hodWelcomeDescription"
            );


        if (
            description &&
            data.department
        ) {

            description.textContent =
                "Manage teachers, monitor attendance, " +
                "approve leave requests, publish notices, " +
                "track performance and generate reports for " +
                data.department +
                " Department.";
        }
    }

    catch (error) {

        console.error(
            "HOD Dashboard Data Error:",
            error
        );
    }
}


/* ============================================================
   REAL HOD PROFILE
============================================================ */

function displayRealHodProfile(
    hod
) {

    const hodName =
        hod.full_name ||
        "HOD";


    const profileName =
        document.querySelector(
            ".profile span"
        );


    if (profileName) {

        profileName.textContent =
            "Welcome, " +
            hodName;
    }


    const heading =
        document.getElementById(
            "hodWelcomeHeading"
        );


    if (heading) {

        heading.textContent =
            "Welcome Back, " +
            hodName +
            " 👋";
    }


    const profileImage =
        document.querySelector(
            ".profile img"
        );


    if (profileImage) {

        if (hod.photo_url) {

            if (
                String(
                    hod.photo_url
                ).startsWith("http")
            ) {

                profileImage.src =
                    hod.photo_url;
            }

            else {

                profileImage.src =
                    "http://127.0.0.1:5000" +
                    hod.photo_url;
            }
        }

        else {

            profileImage.src =
                "../../images/logo.png";
        }
    }
}


/* ============================================================
   COUNTER HELPER
============================================================ */

function setCounterTarget(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {
        return;
    }


    const number =
        Number(value);


    const safeValue =
        Number.isFinite(number)
            ? number
            : 0;


    element.setAttribute(
        "data-target",
        String(safeValue)
    );


    element.textContent =
        "0";
}


/* ============================================================
   COUNTER ANIMATION
============================================================ */

function setupCounters() {

    const counters =
        document.querySelectorAll(
            ".counter"
        );


    counters.forEach(
        function (counter) {

            const target =
                Number(
                    counter.getAttribute(
                        "data-target"
                    )
                ) || 0;


            if (target <= 0) {

                counter.textContent =
                    "0";

                return;
            }


            let count = 0;


            const increment =
                Math.max(
                    1,
                    Math.ceil(
                        target / 70
                    )
                );


            function updateCounter() {

                count += increment;


                if (count < target) {

                    counter.textContent =
                        String(count);


                    setTimeout(
                        updateCounter,
                        20
                    );
                }

                else {

                    counter.textContent =
                        String(target);
                }
            }


            counter.textContent =
                "0";


            updateCounter();
        }
    );
}


/* ============================================================
   PENDING LEAVE REQUESTS
============================================================ */

async function loadPendingLeaveRequests() {

    const tbody =
        document.getElementById(
            "hodPendingLeaveTableBody"
        );


    try {

        const response =
            await API.request(
                "GET",
                "/leave-requests/hod",
                null,
                {
                    status: "pending"
                }
            );


        if (
            !response ||
            response.success !== true
        ) {

            throw new Error(
                response?.message ||
                "Unable to load leave requests."
            );
        }


        const leaves =
            Array.isArray(
                response.data
            )
                ? response.data
                : [];


        const pendingCount =
            Number(
                response.summary
                    ?.pending || 0
            );


        const pendingCounter =
            document.getElementById(
                "hodPendingRequests"
            );


        if (pendingCounter) {

            pendingCounter.setAttribute(
                "data-target",
                String(pendingCount)
            );


            pendingCounter.textContent =
                String(pendingCount);
        }


        if (!tbody) {
            return;
        }


        if (leaves.length === 0) {

            tbody.innerHTML = `
                <tr>
                    <td
                        colspan="4"
                        class="text-center py-4 text-muted">
                        No pending leave requests
                    </td>
                </tr>
            `;

            return;
        }


        tbody.innerHTML =
            leaves
                .map(
                    function (leave) {

                        const dateText =
                            formatLeaveDateRange(
                                leave.start_date,
                                leave.end_date
                            );


                        return `
                            <tr>

                                <td>
                                    ${escapeHtml(
                                        leave.teacher_name ||
                                        "-"
                                    )}
                                </td>

                                <td>
                                    ${dateText}
                                </td>

                                <td>

                                    <strong>
                                        ${escapeHtml(
                                            leave.leave_type ||
                                            "-"
                                        )}
                                    </strong>

                                    ${
                                        leave.reason
                                            ? `
                                                <br>
                                                <small class="text-muted">
                                                    ${escapeHtml(
                                                        leave.reason
                                                    )}
                                                </small>
                                              `
                                            : ""
                                    }

                                </td>

                                <td>

                                    <button
                                        type="button"
                                        class="btn btn-success btn-sm me-1"
                                        onclick="updateHodLeaveStatus(
                                            ${Number(leave.id)},
                                            'approved'
                                        )">

                                        Approve

                                    </button>

                                    <button
                                        type="button"
                                        class="btn btn-danger btn-sm"
                                        onclick="updateHodLeaveStatus(
                                            ${Number(leave.id)},
                                            'rejected'
                                        )">

                                        Reject

                                    </button>

                                </td>

                            </tr>
                        `;
                    }
                )
                .join("");
    }

    catch (error) {

        console.error(
            "Pending Leave Error:",
            error
        );


        if (tbody) {

            tbody.innerHTML = `
                <tr>
                    <td
                        colspan="4"
                        class="text-center text-danger py-4">
                        Unable to load leave requests
                    </td>
                </tr>
            `;
        }
    }
}


/* ============================================================
   APPROVE / REJECT LEAVE
============================================================ */

async function updateHodLeaveStatus(
    leaveId,
    status
) {

    const action =
        status === "approved"
            ? "approve"
            : "reject";


    const confirmed =
        confirm(
            `Are you sure you want to ${action} this leave request?`
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await API.request(
                "PATCH",
                `/leave-requests/${leaveId}/status`,
                {
                    status: status,
                    hod_remarks: ""
                }
            );


        if (
            !response ||
            response.success !== true
        ) {

            throw new Error(
                response?.message ||
                "Unable to update leave request."
            );
        }


        alert(
            response.message ||
            "Leave request updated successfully."
        );


        await loadPendingLeaveRequests();

        /*
         * Refresh analytics because pending leave
         * totals may have changed.
         */
        await loadDashboardAnalytics();
    }

    catch (error) {

        console.error(
            "Leave Update Error:",
            error
        );


        alert(
            error.message ||
            "Unable to update leave request."
        );
    }
}


/* ============================================================
   REAL ANALYTICS
============================================================ */

async function loadDashboardAnalytics() {

    try {

        const response =
            await API.request(
                "GET",
                "/hods/analytics"
            );


        console.log(
            "HOD Analytics:",
            response
        );


        if (
            !response ||
            response.success !== true
        ) {

            throw new Error(
                response?.message ||
                "Unable to load analytics."
            );
        }


        window.currentHodAnalyticsData =
            response;


        renderAttendanceChart(
            response.attendance || {}
        );


        renderPerformanceChart(
            response.performance || {}
        );
    }

    catch (error) {

        console.error(
            "HOD Analytics Error:",
            error
        );


        renderAttendanceChart(
            {
                trend: []
            }
        );


        renderPerformanceChart(
            {
                distribution: {}
            }
        );
    }
}


/* ============================================================
   REAL ATTENDANCE CHART
============================================================ */

function renderAttendanceChart(
    attendance
) {

    const canvas =
        document.getElementById(
            "attendanceChart"
        );


    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }


    if (attendanceChartInstance) {

        attendanceChartInstance.destroy();
    }


    const trend =
        Array.isArray(
            attendance.trend
        )
            ? attendance.trend
            : [];


    const recentTrend =
        trend.slice(-7);


    let labels = [];
    let percentages = [];


    if (recentTrend.length > 0) {

        labels =
            recentTrend.map(
                function (item) {

                    return formatShortDate(
                        item.date
                    );
                }
            );


        percentages =
            recentTrend.map(
                function (item) {

                    const total =
                        Number(
                            item.total
                        ) || 0;


                    const present =
                        Number(
                            item.present
                        ) || 0;


                    if (total <= 0) {
                        return 0;
                    }


                    return Number(
                        (
                            (
                                present /
                                total
                            ) * 100
                        ).toFixed(1)
                    );
                }
            );
    }

    else {

        labels = [
            "No Records"
        ];

        percentages = [
            0
        ];
    }


    attendanceChartInstance =
        new Chart(
            canvas,
            {

                type: "bar",

                data: {

                    labels: labels,

                    datasets: [
                        {
                            label:
                                "Attendance %",

                            data:
                                percentages,

                            backgroundColor:
                                "#6c4cff",

                            borderRadius:
                                8
                        }
                    ]
                },

                options: {

                    responsive:
                        true,

                    maintainAspectRatio:
                        true,

                    scales: {

                        y: {

                            beginAtZero:
                                true,

                            max:
                                100,

                            ticks: {

                                callback:
                                    function (value) {

                                        return (
                                            value +
                                            "%"
                                        );
                                    }
                            }
                        }
                    },

                    plugins: {

                        legend: {

                            display:
                                false
                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    function (context) {

                                        return (
                                            context.raw +
                                            "%"
                                        );
                                    }
                            }
                        }
                    }
                }
            }
        );
}


/* ============================================================
   REAL FACULTY PERFORMANCE CHART
============================================================ */

function renderPerformanceChart(
    performance
) {

    const canvas =
        document.getElementById(
            "performanceChart"
        );


    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }


    if (performanceChartInstance) {

        performanceChartInstance.destroy();
    }


    const distribution =
        performance.distribution || {};


    const chartData = [
        Number(
            distribution.excellent
        ) || 0,

        Number(
            distribution.good
        ) || 0,

        Number(
            distribution.average
        ) || 0,

        Number(
            distribution.poor
        ) || 0
    ];


    performanceChartInstance =
        new Chart(
            canvas,
            {

                type:
                    "doughnut",

                data: {

                    labels: [
                        "Excellent",
                        "Good",
                        "Average",
                        "Poor"
                    ],

                    datasets: [
                        {
                            data:
                                chartData,

                            backgroundColor: [
                                "#6c4cff",
                                "#4CAF50",
                                "#FFC107",
                                "#F44336"
                            ]
                        }
                    ]
                },

                options: {

                    responsive:
                        true,

                    plugins: {

                        legend: {

                            position:
                                "bottom"
                        }
                    }
                }
            }
        );
}


/* ============================================================
   REAL TEACHER PERFORMANCE TABLE
============================================================ */

async function loadTeacherPerformance() {

    const tbody =
        getTeacherPerformanceTableBody();


    if (!tbody) {
        return;
    }


    try {

        const response =
            await API.request(
                "GET",
                "/hods/performance"
            );


        console.log(
            "HOD Performance:",
            response
        );


        if (
            !response ||
            response.success !== true
        ) {

            throw new Error(
                response?.message ||
                "Unable to load performance."
            );
        }


        const records =
            Array.isArray(
                response.data
            )
                ? response.data
                : [];


        if (records.length === 0) {

            tbody.innerHTML = `
                <tr>
                    <td
                        colspan="3"
                        class="text-center py-4 text-muted">
                        No performance records available
                    </td>
                </tr>
            `;

            return;
        }


        /*
         * Latest four real performance records.
         */
        const latestRecords =
            records.slice(0, 4);


        tbody.innerHTML =
            latestRecords
                .map(
                    function (record) {

                        const band =
                            record.band ||
                            "Not Rated";


                        const badgeClass =
                            getPerformanceBadgeClass(
                                band
                            );


                        const percentage =
                            Number.isFinite(
                                Number(
                                    record.percentage
                                )
                            )
                                ? Number(
                                    record.percentage
                                ).toFixed(1)
                                : null;


                        return `
                            <tr>

                                <td>
                                    ${escapeHtml(
                                        record.teacher_name ||
                                        "-"
                                    )}
                                </td>

                                <td>
                                    ${escapeHtml(
                                        record.subject ||
                                        "-"
                                    )}
                                </td>

                                <td>

                                    <span
                                        class="badge ${badgeClass}">

                                        ${escapeHtml(
                                            band
                                        )}

                                        ${
                                            percentage !== null
                                                ? ` (${percentage}%)`
                                                : ""
                                        }

                                    </span>

                                </td>

                            </tr>
                        `;
                    }
                )
                .join("");
    }

    catch (error) {

        console.error(
            "Teacher Performance Error:",
            error
        );


        tbody.innerHTML = `
            <tr>
                <td
                    colspan="3"
                    class="text-center text-danger py-4">
                    Unable to load performance records
                </td>
            </tr>
        `;
    }
}


/* ============================================================
   FIND TEACHER PERFORMANCE TABLE BODY
============================================================ */

function getTeacherPerformanceTableBody() {

    const firstDashboardCard =
        document.querySelector(
            ".content-grid .dashboard-card"
        );


    if (!firstDashboardCard) {
        return null;
    }


    return firstDashboardCard
        .querySelector(
            "table tbody"
        );
}


/* ============================================================
   PERFORMANCE BADGE
============================================================ */

function getPerformanceBadgeClass(
    band
) {

    const value =
        String(
            band || ""
        ).toLowerCase();


    if (value === "excellent") {

        return "bg-success";
    }


    if (value === "good") {

        return "bg-primary";
    }


    if (value === "average") {

        return "bg-warning text-dark";
    }


    if (value === "poor") {

        return "bg-danger";
    }


    return "bg-secondary";
}


/* ============================================================
   REAL TEACHER OVERVIEW
============================================================ */

async function loadTeacherOverview() {

    const canvas =
        document.getElementById(
            "teacherOverviewChart"
        );


    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }


    try {

        const response =
            await API.request(
                "GET",
                "/hods/teachers"
            );


        console.log(
            "HOD Teachers:",
            response
        );


        if (
            !response ||
            response.success !== true
        ) {

            throw new Error(
                response?.message ||
                "Unable to load teachers."
            );
        }


        const teachers =
            Array.isArray(
                response.data
            )
                ? response.data
                : [];


        const activeTeachers =
            teachers.filter(
                function (teacher) {

                    return (
                        String(
                            teacher.status ||
                            ""
                        )
                            .trim()
                            .toLowerCase()
                        === "active"
                    );
                }
            ).length;


        const inactiveTeachers =
            Math.max(
                teachers.length -
                activeTeachers,
                0
            );


        renderTeacherOverviewChart(
            activeTeachers,
            inactiveTeachers
        );
    }

    catch (error) {

        console.error(
            "Teacher Overview Error:",
            error
        );


        renderTeacherOverviewChart(
            0,
            0
        );
    }
}


/* ============================================================
   TEACHER OVERVIEW CHART
============================================================ */

function renderTeacherOverviewChart(
    activeTeachers,
    inactiveTeachers
) {

    const canvas =
        document.getElementById(
            "teacherOverviewChart"
        );


    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }


    if (teacherOverviewChartInstance) {

        teacherOverviewChartInstance
            .destroy();
    }


    teacherOverviewChartInstance =
        new Chart(
            canvas,
            {

                type:
                    "doughnut",

                data: {

                    labels: [
                        "Active",
                        "Inactive"
                    ],

                    datasets: [
                        {
                            data: [
                                activeTeachers,
                                inactiveTeachers
                            ],

                            backgroundColor: [
                                "#6c4cff",
                                "#cbd5e1"
                            ]
                        }
                    ]
                },

                options: {

                    responsive:
                        true,

                    maintainAspectRatio:
                        false,

                    plugins: {

                        legend: {

                            position:
                                "bottom"
                        }
                    }
                }
            }
        );
}


/* ============================================================
   REAL NOTIFICATIONS
============================================================ */

async function loadDashboardNotifications() {

    try {

        const response =
            await API.request(
                "GET",
                "/notifications"
            );


        console.log(
            "HOD Notifications:",
            response
        );


        if (
            !response ||
            response.success !== true
        ) {

            throw new Error(
                response?.message ||
                "Unable to load notifications."
            );
        }


        const notifications =
            Array.isArray(
                response.data
            )
                ? response.data
                : [];


        window.currentHodNotifications =
            notifications;


        const unread =
            Number(
                response.summary
                    ?.unread || 0
            );


        renderNotificationCount(
            unread
        );


        renderTopNotificationDropdown(
            notifications,
            unread
        );


        renderRecentActivities(
            notifications
        );


        renderBottomNotifications(
            notifications
        );
    }

    catch (error) {

        console.error(
            "Notification Error:",
            error
        );


        renderNotificationCount(
            0
        );


        renderTopNotificationDropdown(
            [],
            0
        );


        renderRecentActivities(
            []
        );


        renderBottomNotifications(
            []
        );
    }
}


/* ============================================================
   NOTIFICATION BADGE
============================================================ */

function renderNotificationCount(
    unread
) {

    const badge =
        document.getElementById(
            "notificationCount"
        );


    if (!badge) {
        return;
    }


    const count =
        Number(unread) || 0;


    badge.textContent =
        String(count);


    badge.style.display =
        count > 0
            ? "flex"
            : "none";
}


/* ============================================================
   TOP NOTIFICATION DROPDOWN
============================================================ */

function renderTopNotificationDropdown(
    notifications,
    unread
) {

    const menu =
        document.querySelector(
            ".notification-menu"
        );


    if (!menu) {
        return;
    }


    const latest =
        notifications.slice(0, 4);


    let notificationHtml = "";


    if (latest.length === 0) {

        notificationHtml = `
            <li>
                <div
                    class="dropdown-item text-muted text-center">
                    No notifications
                </div>
            </li>
        `;
    }

    else {

        notificationHtml =
            latest
                .map(
                    function (notification) {

                        const unreadStyle =
                            notification.is_read
                                ? ""
                                : "fw-semibold";


                        return `
                            <li>

                                <a
                                    href="#"
                                    class="dropdown-item notification-item ${unreadStyle}"
                                    onclick="
                                        openDashboardNotification(
                                            event,
                                            ${Number(notification.id)}
                                        )
                                    ">

                                    ${getNotificationEmoji(
                                        notification.category
                                    )}

                                    ${escapeHtml(
                                        notification.title ||
                                        "Notification"
                                    )}

                                </a>

                            </li>
                        `;
                    }
                )
                .join("");
    }


    menu.innerHTML = `

        <li class="dropdown-header">

            Notifications

            ${
                unread > 0
                    ? `<span class="float-end">
                           ${unread} unread
                       </span>`
                    : ""
            }

        </li>


        ${notificationHtml}


        <li>
            <hr class="dropdown-divider">
        </li>


        <li>

            <a
                href="#"
                class="dropdown-item text-center"
                id="markAllRead">

                Mark All as Read

            </a>

        </li>


        <li>

            <a
                href="notification.html"
                class="dropdown-item text-center">

                View All Notifications

            </a>

        </li>
    `;


    bindMarkAllRead();
}


/* ============================================================
   OPEN NOTIFICATION
============================================================ */

async function openDashboardNotification(
    event,
    notificationId
) {

    if (event) {
        event.preventDefault();
    }


    try {

        await API.request(
            "PATCH",
            `/notifications/${notificationId}/read`,
            {}
        );
    }

    catch (error) {

        console.error(
            "Mark Notification Read Error:",
            error
        );
    }


    window.location.href =
        "notification.html";
}


/* ============================================================
   MARK ALL NOTIFICATIONS READ
============================================================ */

function bindMarkAllRead() {

    const button =
        document.getElementById(
            "markAllRead"
        );


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        async function (event) {

            event.preventDefault();


            try {

                const response =
                    await API.request(
                        "PATCH",
                        "/notifications/read-all",
                        {}
                    );


                if (
                    !response ||
                    response.success !== true
                ) {

                    throw new Error(
                        response?.message ||
                        "Unable to mark notifications as read."
                    );
                }


                await loadDashboardNotifications();
            }

            catch (error) {

                console.error(
                    "Mark All Read Error:",
                    error
                );


                alert(
                    error.message ||
                    "Unable to mark notifications as read."
                );
            }
        }
    );
}


/* ============================================================
   RECENT ACTIVITIES
============================================================ */

function renderRecentActivities(
    notifications
) {

    const lists =
        document.querySelectorAll(
            ".activity-list"
        );


    if (lists.length === 0) {
        return;
    }


    const list =
        lists[0];


    const recent =
        notifications.slice(0, 4);


    if (recent.length === 0) {

        list.innerHTML = `
            <li class="text-muted">
                No recent activities available
            </li>
        `;

        return;
    }


    list.innerHTML =
        recent
            .map(
                function (notification) {

                    return `
                        <li>

                            <i
                                class="${getNotificationIcon(
                                    notification.category
                                )}">
                            </i>

                            <div>

                                <div>
                                    ${escapeHtml(
                                        notification.title ||
                                        "Activity"
                                    )}
                                </div>

                                <small class="text-muted">
                                    ${formatDateTime(
                                        notification.created_at
                                    )}
                                </small>

                            </div>

                        </li>
                    `;
                }
            )
            .join("");
}


/* ============================================================
   BOTTOM NOTIFICATION CARD
============================================================ */

function renderBottomNotifications(
    notifications
) {

    const lists =
        document.querySelectorAll(
            ".activity-list"
        );


    if (lists.length < 2) {
        return;
    }


    const list =
        lists[1];


    const latest =
        notifications.slice(0, 5);


    if (latest.length === 0) {

        list.innerHTML = `
            <li class="text-muted">
                No notifications available
            </li>
        `;

        return;
    }


    list.innerHTML =
        latest
            .map(
                function (notification) {

                    return `
                        <li>

                            ${getNotificationEmoji(
                                notification.category
                            )}

                            <div>

                                <div>
                                    ${escapeHtml(
                                        notification.title ||
                                        "Notification"
                                    )}
                                </div>

                                ${
                                    notification.message
                                        ? `
                                            <small class="text-muted">
                                                ${escapeHtml(
                                                    shortenText(
                                                        notification.message,
                                                        65
                                                    )
                                                )}
                                            </small>
                                          `
                                        : ""
                                }

                            </div>

                        </li>
                    `;
                }
            )
            .join("");
}


/* ============================================================
   NOTIFICATION CATEGORY ICON
============================================================ */

function getNotificationIcon(
    category
) {

    const value =
        String(
            category || ""
        )
            .trim()
            .toLowerCase();


    if (
        value.includes("notice") ||
        value.includes("announcement")
    ) {

        return (
            "fa-solid fa-bullhorn " +
            "text-danger"
        );
    }


    if (
        value.includes("leave")
    ) {

        return (
            "fa-solid fa-file-circle-check " +
            "text-warning"
        );
    }


    if (
        value.includes("calendar") ||
        value.includes("event")
    ) {

        return (
            "fa-solid fa-calendar-check " +
            "text-success"
        );
    }


    if (
        value.includes("performance")
    ) {

        return (
            "fa-solid fa-chart-line " +
            "text-primary"
        );
    }


    return (
        "fa-solid fa-bell " +
        "text-primary"
    );
}


/* ============================================================
   NOTIFICATION EMOJI
============================================================ */

function getNotificationEmoji(
    category
) {

    const value =
        String(
            category || ""
        )
            .trim()
            .toLowerCase();


    if (
        value.includes("notice") ||
        value.includes("announcement")
    ) {
        return "📢";
    }


    if (
        value.includes("leave")
    ) {
        return "📄";
    }


    if (
        value.includes("calendar") ||
        value.includes("event")
    ) {
        return "📅";
    }


    if (
        value.includes("performance")
    ) {
        return "📊";
    }


    return "🔔";
}


/* ============================================================
   REAL ACADEMIC CALENDAR
============================================================ */

async function setupCalendar() {

    const calendarElement =
        document.getElementById(
            "calendar"
        );


    if (
        !calendarElement ||
        typeof FullCalendar === "undefined"
    ) {
        return;
    }


    try {

        /*
         * IMPORTANT:
         *
         * Use HOD-specific endpoint.
         *
         * Backend itself already restricts this to:
         * - Global/Admin events
         * - Logged-in HOD department events
         */
        const response =
            await API.request(
                "GET",
                "/academic-events/hod"
            );


        console.log(
            "HOD Academic Events:",
            response
        );


        if (
            !response ||
            response.success !== true
        ) {

            throw new Error(
                response?.message ||
                "Unable to load academic calendar."
            );
        }


        const events =
            Array.isArray(
                response.data
            )
                ? response.data
                : [];


        const fullCalendarEvents =
            events.map(
                function (event) {

                    return {

                        id:
                            String(
                                event.id
                            ),

                        title:
                            event.title ||
                            "Academic Event",

                        start:
                            event.start_date,

                        end:
                            addOneDay(
                                event.end_date ||
                                event.start_date
                            ),

                        allDay:
                            true,

                        extendedProps: {

                            description:
                                event.description ||
                                "",

                            eventType:
                                event.event_type ||
                                "event",

                            department:
                                event.department ||
                                "All Departments",

                            status:
                                event.status ||
                                "",

                            scope:
                                event.scope ||
                                ""
                        }
                    };
                }
            );


        if (hodCalendarInstance) {

            hodCalendarInstance
                .destroy();
        }


        calendarElement.innerHTML =
            "";


        hodCalendarInstance =
            new FullCalendar.Calendar(
                calendarElement,
                {

                    initialView:
                        "dayGridMonth",

                    height:
                        400,

                    events:
                        fullCalendarEvents,

                    dayMaxEvents:
                         false,

                     dayMaxEventRows:
                        false,     

                    eventClick:
                        function (info) {

                            info.jsEvent
                                .preventDefault();


                            window.location.href =
                                "academic-calendar.html";
                        }
                }
            );


        hodCalendarInstance
            .render();
    }

    catch (error) {

        console.error(
            "Academic Calendar Error:",
            error
        );


        calendarElement.innerHTML = `
            <div
                class="text-center text-danger py-5">
                Unable to load academic calendar
            </div>
        `;
    }
}


/* ============================================================
   FULLCALENDAR EXCLUSIVE END DATE
============================================================ */

function addOneDay(
    dateString
) {

    if (!dateString) {
        return null;
    }


    const parts =
        String(
            dateString
        ).split("-");


    if (parts.length !== 3) {
        return dateString;
    }


    const year =
        Number(parts[0]);

    const month =
        Number(parts[1]);

    const day =
        Number(parts[2]);


    const date =
        new Date(
            Date.UTC(
                year,
                month - 1,
                day
            )
        );


    date.setUTCDate(
        date.getUTCDate() + 1
    );


    return date
        .toISOString()
        .slice(0, 10);
}


/* ============================================================
   LIVE CLOCK
============================================================ */

function setupClock() {

    function updateClock() {

        const now =
            new Date();


        const liveTime =
            document.getElementById(
                "liveTime"
            );


        const liveDate =
            document.getElementById(
                "liveDate"
            );


        if (liveTime) {

            liveTime.textContent =
                now.toLocaleTimeString(
                    "en-IN",
                    {
                        hour:
                            "2-digit",

                        minute:
                            "2-digit",

                        second:
                            "2-digit"
                    }
                );
        }


        if (liveDate) {

            liveDate.textContent =
                now.toLocaleDateString(
                    "en-GB",
                    {
                        weekday:
                            "long",

                        day:
                            "numeric",

                        month:
                            "long",

                        year:
                            "numeric"
                    }
                );
        }
    }


    updateClock();


    setInterval(
        updateClock,
        1000
    );
}


/* ============================================================
   SEARCH
============================================================ */

function setupSearch() {

    const searchBox =
        document.getElementById(
            "searchBox"
        );


    if (!searchBox) {
        return;
    }


    searchBox.addEventListener(
        "keyup",
        function () {

            const value =
                this.value
                    .toLowerCase()
                    .trim();


            document
                .querySelectorAll(
                    ".card-box, " +
                    ".dashboard-card, " +
                    ".quick-actions"
                )
                .forEach(
                    function (card) {

                        const text =
                            card.innerText
                                .toLowerCase();


                        card.style.display =
                            text.includes(
                                value
                            )
                                ? ""
                                : "none";
                    }
                );
        }
    );
}


/* ============================================================
   DARK / LIGHT THEME
============================================================ */

function setupTheme() {

    const themeToggle =
        document.getElementById(
            "themeToggle"
        );


    const savedTheme =
        localStorage.getItem(
            "hodTheme"
        );


    if (savedTheme === "dark") {

        document.body.classList.add(
            "dark"
        );
    }

    else {

        document.body.classList.remove(
            "dark"
        );
    }


    function updateThemeIcon() {

        if (!themeToggle) {
            return;
        }


        const icon =
            themeToggle.querySelector(
                "i"
            );


        if (!icon) {
            return;
        }


        if (
            document.body.classList
                .contains(
                    "dark"
                )
        ) {

            icon.classList.remove(
                "fa-moon"
            );

            icon.classList.add(
                "fa-sun"
            );


            themeToggle.title =
                "Switch to Light Mode";
        }

        else {

            icon.classList.remove(
                "fa-sun"
            );

            icon.classList.add(
                "fa-moon"
            );


            themeToggle.title =
                "Switch to Dark Mode";
        }
    }


    updateThemeIcon();


    if (!themeToggle) {
        return;
    }


    themeToggle.addEventListener(
        "click",
        function () {

            document.body.classList
                .toggle(
                    "dark"
                );


            const isDark =
                document.body.classList
                    .contains(
                        "dark"
                    );


            localStorage.setItem(
                "hodTheme",
                isDark
                    ? "dark"
                    : "light"
            );


            updateThemeIcon();
        }
    );
}


/* ============================================================
   REAL DASHBOARD CSV EXPORT
============================================================ */

function setupExportData() {

    const exportButton =
        document.querySelector(
            ".action-buttons .btn-danger"
        );


    if (!exportButton) {
        return;
    }


    exportButton.addEventListener(
        "click",
        function () {

            const dashboard =
                window.currentHodDashboardData ||
                {};


            const analytics =
                window.currentHodAnalyticsData ||
                {};


            const rows = [

                [
                    "Metric",
                    "Value"
                ],

                [
                    "Department",
                    dashboard.department ||
                    "-"
                ],

                [
                    "Total Teachers",
                    dashboard.total_teachers ??
                    0
                ],

                [
                    "Total Students",
                    dashboard.total_students ??
                    0
                ],

                [
                    "Attendance Percentage",
                    (
                        analytics.attendance
                            ?.percentage ??
                        0
                    ) + "%"
                ],

                [
                    "Average Performance",
                    (
                        analytics.performance
                            ?.average_percentage ??
                        0
                    ) + "%"
                ],

                [
                    "Pending Leave Requests",
                    analytics.leave_requests
                        ?.pending ??
                    0
                ]
            ];


            const csv =
                rows
                    .map(
                        function (row) {

                            return row
                                .map(
                                    csvEscape
                                )
                                .join(",");
                        }
                    )
                    .join("\n");


            const blob =
                new Blob(
                    [csv],
                    {
                        type:
                            "text/csv;charset=utf-8;"
                    }
                );


            const url =
                URL.createObjectURL(
                    blob
                );


            const link =
                document.createElement(
                    "a"
                );


            link.href =
                url;


            link.download =
                "hod_dashboard_summary_" +
                new Date()
                    .toISOString()
                    .slice(0, 10) +
                ".csv";


            document.body.appendChild(
                link
            );


            link.click();


            document.body.removeChild(
                link
            );


            URL.revokeObjectURL(
                url
            );
        }
    );
}


/* ============================================================
   CSV ESCAPE
============================================================ */

function csvEscape(
    value
) {

    const text =
        String(
            value ?? ""
        );


    return (
        '"' +
        text.replaceAll(
            '"',
            '""'
        ) +
        '"'
    );
}


/* ============================================================
   LOGOUT
============================================================ */

function setupLogout() {

    const logoutLinks =
        document.querySelectorAll(
            ".hod-logout-link"
        );


    logoutLinks.forEach(
        function (logoutLink) {

            logoutLink.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();


                    if (
                        typeof API !== "undefined" &&
                        API.auth
                    ) {

                        API.auth.logout();
                    }

                    else {

                        localStorage.removeItem(
                            "fmps_access_token"
                        );

                        localStorage.removeItem(
                            "fmps_user"
                        );
                    }


                    window.location.href =
                        "hod-login.html";
                }
            );
        }
    );
}


/* ============================================================
   DATE HELPERS
============================================================ */

function formatLeaveDateRange(
    startDate,
    endDate
) {

    const start =
        formatDate(
            startDate
        );


    if (
        !endDate ||
        endDate === startDate
    ) {

        return start;
    }


    return (
        start +
        " - " +
        formatDate(
            endDate
        )
    );
}


function formatDate(
    dateString
) {

    if (!dateString) {
        return "-";
    }


    const date =
        new Date(
            dateString +
            "T00:00:00"
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return dateString;
    }


    return date.toLocaleDateString(
        "en-GB",
        {
            day:
                "2-digit",

            month:
                "short",

            year:
                "numeric"
        }
    );
}


function formatShortDate(
    dateString
) {

    if (!dateString) {
        return "-";
    }


    const date =
        new Date(
            dateString +
            "T00:00:00"
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return dateString;
    }


    return date.toLocaleDateString(
        "en-GB",
        {
            day:
                "2-digit",

            month:
                "short"
        }
    );
}


function formatDateTime(
    dateString
) {

    if (!dateString) {
        return "";
    }


    const date =
        new Date(
            dateString
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return "";
    }


    return date.toLocaleString(
        "en-IN",
        {
            day:
                "2-digit",

            month:
                "short",

            hour:
                "2-digit",

            minute:
                "2-digit"
        }
    );
}


/* ============================================================
   TEXT HELPERS
============================================================ */

function shortenText(
    value,
    maxLength
) {

    const text =
        String(
            value || ""
        );


    if (
        text.length <= maxLength
    ) {

        return text;
    }


    return (
        text.slice(
            0,
            maxLength
        ) +
        "..."
    );
}


/* ============================================================
   SAFE HTML
============================================================ */

function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}