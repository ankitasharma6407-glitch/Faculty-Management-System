// ============================================================
// FMPS ADMIN DASHBOARD COMMON JAVASCRIPT
// Faculty Management & Productivity System
// ============================================================


// ============================================================
// THEME FUNCTIONS
// ============================================================

function applySavedTheme() {

    const savedTheme =
        localStorage.getItem("theme") || "light";

    const themeToggle =
        document.getElementById("themeToggle");

    const themeMenu =
        document.getElementById("themeMenu");


    if (savedTheme === "dark") {

        document.body.classList.add("dark");

        if (themeToggle) {

            themeToggle.innerHTML =
                '<i class="fa-solid fa-sun"></i>';

            themeToggle.setAttribute(
                "title",
                "Switch to Light Mode"
            );

        }


        if (themeMenu) {

            themeMenu.innerHTML =
                '<i class="fa-solid fa-sun"></i> Light Mode';

        }

    }

    else {

        document.body.classList.remove("dark");

        if (themeToggle) {

            themeToggle.innerHTML =
                '<i class="fa-solid fa-moon"></i>';

            themeToggle.setAttribute(
                "title",
                "Switch to Dark Mode"
            );

        }


        if (themeMenu) {

            themeMenu.innerHTML =
                '<i class="fa-solid fa-moon"></i> Dark Mode';

        }

    }

}



// ============================================================
// TOGGLE THEME
// ============================================================

function toggleTheme() {

    const currentTheme =
        localStorage.getItem("theme") || "light";


    const newTheme =
        currentTheme === "dark"
            ? "light"
            : "dark";


    localStorage.setItem(
        "theme",
        newTheme
    );


    applySavedTheme();

}


// ============================================================
// APPLY THEME EARLY
// ============================================================

applySavedTheme();



// ============================================================
// SYNC THEME BETWEEN OPEN PAGES / TABS
// ============================================================

window.addEventListener(
    "storage",
    function (event) {

        if (event.key === "theme") {

            applySavedTheme();

        }

    }
);



// ============================================================
// FIX BACK / FORWARD PAGE CACHE
// ============================================================

window.addEventListener(
    "pageshow",
    function () {

        applySavedTheme();

    }
);



// ============================================================
// DOM READY
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {


        // ====================================================
        // ELEMENTS
        // ====================================================

        const themeToggle =
            document.getElementById(
                "themeToggle"
            );


        const themeMenu =
            document.getElementById(
                "themeMenu"
            );


        const profileBtn =
            document.getElementById(
                "profileBtn"
            );


        const profileDropdown =
            document.getElementById(
                "profileDropdown"
            );


        const greeting =
            document.getElementById(
                "greeting"
            );


        const searchBox =
            document.getElementById(
                "searchBox"
            );


        const markAllRead =
            document.getElementById(
                "markAllRead"
            );


        const notificationCount =
            document.getElementById(
                "notificationCount"
            );



        // ====================================================
        // APPLY SAVED THEME AGAIN AFTER DOM LOAD
        // ====================================================

        applySavedTheme();



        // ====================================================
        // GREETING
        // ====================================================

        if (greeting) {

            const hour =
                new Date().getHours();


            if (hour < 12) {

                greeting.innerHTML =
                    "Good Morning ☀️";

            }

            else if (hour < 17) {

                greeting.innerHTML =
                    "Good Afternoon 🌤️";

            }

            else {

                greeting.innerHTML =
                    "Good Evening 🌙";

            }

        }



        // ====================================================
        // THEME TOGGLE BUTTON
        // ====================================================

        if (themeToggle) {

            themeToggle.addEventListener(
                "click",
                function () {

                    toggleTheme();

                }
            );

        }



        // ====================================================
        // PROFILE THEME MENU
        // ====================================================

        if (themeMenu) {

            themeMenu.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    toggleTheme();

                }
            );

        }



        // ====================================================
        // PROFILE DROPDOWN
        // ====================================================

        if (
            profileBtn &&
            profileDropdown
        ) {

            profileBtn.addEventListener(
                "click",
                function (event) {

                    event.stopPropagation();

                    profileDropdown.classList.toggle(
                        "show"
                    );

                }
            );


            profileDropdown.addEventListener(
                "click",
                function (event) {

                    event.stopPropagation();

                }
            );

        }



        document.addEventListener(
            "click",
            function () {

                if (profileDropdown) {

                    profileDropdown.classList.remove(
                        "show"
                    );

                }

            }
        );



        // ====================================================
        // DASHBOARD SEARCH
        // ====================================================

        if (searchBox) {

            searchBox.addEventListener(
                "input",
                function () {


                    const value =
                        this.value
                            .trim()
                            .toLowerCase();


                    const cards =
                        document.querySelectorAll(
                            ".stat-card, " +
                            ".quick-card, " +
                            ".chart-card, " +
                            ".calendar-card, " +
                            ".activity-card, " +
                            ".table-card, " +
                            ".notification-panel"
                        );


                    cards.forEach(
                        function (card) {


                            const text =
                                card.innerText
                                    .toLowerCase();


                            card.style.display =
                                !value ||
                                text.includes(value)
                                    ? ""
                                    : "none";

                        }
                    );

                }
            );

        }



        // ====================================================
        // MARK ALL NOTIFICATIONS READ
        // ====================================================

        if (markAllRead) {

            markAllRead.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();


                    if (notificationCount) {

                        notificationCount.style.display =
                            "none";

                    }

                }
            );

        }



        // ====================================================
        // NOTIFICATION POPUP
        // ====================================================

        document
            .querySelectorAll(
                ".notification-item"
            )
            .forEach(
                function (item) {


                    item.addEventListener(
                        "click",
                        function () {

                            const message =
                                item.innerText.trim();


                            if (message) {

                                alert(
                                    message
                                );

                            }

                        }
                    );

                }
            );



        // ====================================================
        // LOGOUT CONFIRMATION
        // ====================================================

        document
            .querySelectorAll(
                ".logout-btn, .logout-link"
            )
            .forEach(
                function (button) {


                    button.addEventListener(
                        "click",
                        function (event) {


                            const confirmed =
                                confirm(
                                    "Do you really want to logout?"
                                );


                            if (!confirmed) {

                                event.preventDefault();

                            }

                        }
                    );

                }
            );



        // ====================================================
        // CHANGE PROFILE PHOTO
        // ====================================================

        const changePhoto =
            document.getElementById(
                "changePhoto"
            );


        if (changePhoto) {

            changePhoto.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();


                    alert(
                        "Profile photo upload feature will be available after backend integration."
                    );

                }
            );

        }



        // ====================================================
        // ATTENDANCE CHART
        // ====================================================

        const attendance =
            document.getElementById(
                "attendanceChart"
            );


        if (
            attendance &&
            typeof Chart !== "undefined"
        ) {

            new Chart(
                attendance,
                {

                    type: "bar",

                    data: {

                        labels: [
                            "Jan",
                            "Feb",
                            "Mar",
                            "Apr",
                            "May",
                            "Jun"
                        ],

                        datasets: [

                            {

                                label:
                                    "Attendance %",

                                data: [
                                    92,
                                    95,
                                    91,
                                    96,
                                    94,
                                    98
                                ],

                                backgroundColor: [
                                    "#6b3dff",
                                    "#7b4cff",
                                    "#8b5cff",
                                    "#9b6cff",
                                    "#ab7cff",
                                    "#bb8cff"
                                ],

                                borderRadius:
                                    8

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

                                display:
                                    false

                            }

                        },

                        scales: {

                            y: {

                                beginAtZero:
                                    true,

                                max:
                                    100

                            }

                        }

                    }

                }
            );

        }



        // ====================================================
        // PERFORMANCE CHART
        // ====================================================

        const performance =
            document.getElementById(
                "performanceChart"
            );


        if (
            performance &&
            typeof Chart !== "undefined"
        ) {

            new Chart(
                performance,
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

                                data: [
                                    45,
                                    30,
                                    15,
                                    10
                                ],

                                backgroundColor: [
                                    "#6b3dff",
                                    "#0d6efd",
                                    "#ffc107",
                                    "#dc3545"
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



        // ====================================================
        // DASHBOARD CALENDAR
        // ====================================================

        const calendarEl =
            document.getElementById(
                "calendar"
            );


        if (
            calendarEl &&
            typeof FullCalendar !== "undefined"
        ) {

            const calendar =
                new FullCalendar.Calendar(
                    calendarEl,
                    {

                        initialView:
                            "dayGridMonth",

                        height:
                            500,

                        events: [

                            {

                                title:
                                    "Faculty Meeting",

                                start:
                                    "2026-07-25"

                            },

                            {

                                title:
                                    "Placement Drive",

                                start:
                                    "2026-07-28"

                            },

                            {

                                title:
                                    "Internal Exam",

                                start:
                                    "2026-07-30"

                            }

                        ]

                    }
                );


            calendar.render();

        }



        // ====================================================
        // LOAD ADMIN DASHBOARD DATA
        // ONLY ON ADMIN DASHBOARD PAGE
        // ====================================================

        const totalTeachers =
            document.getElementById(
                "totalTeachers"
            );


        const totalDepartments =
            document.getElementById(
                "totalDepartments"
            );


        const totalRecruiters =
            document.getElementById(
                "totalRecruiters"
            );


        if (
            totalTeachers &&
            totalDepartments &&
            totalRecruiters
        ) {

            loadAdminDashboard();

        }

    }
);



// ============================================================
// ADMIN DASHBOARD API DATA
// ============================================================

async function loadAdminDashboard() {


    if (
        typeof API === "undefined"
    ) {

        console.warn(
            "API client is not available."
        );

        return;

    }


    try {


        const response =
            await API.request(
                "GET",
                "/admin/dashboard"
            );


        console.log(
            "Admin Dashboard Data:",
            response
        );


        if (
            !response ||
            !response.success
        ) {

            console.error(
                "Failed to load dashboard data"
            );

            return;

        }


        const dashboard =
            response.data || {};



        // ====================================================
        // TOTAL TEACHERS
        // ====================================================

        const teacherCount =
            document.getElementById(
                "totalTeachers"
            );


        if (teacherCount) {

            teacherCount.textContent =
                dashboard.teachers ?? 0;

        }



        // ====================================================
        // TOTAL DEPARTMENTS
        // ====================================================

        const departmentCount =
            document.getElementById(
                "totalDepartments"
            );


        if (departmentCount) {

            departmentCount.textContent =
                dashboard.departments ?? 0;

        }



        // ====================================================
        // TOTAL RECRUITERS
        // ====================================================

        const recruiterCount =
            document.getElementById(
                "totalRecruiters"
            );


        if (recruiterCount) {

            recruiterCount.textContent =
                dashboard.recruiters ?? 0;

        }


        // HOD face attendance is stored in FacultyAttendance and is shown
        // directly on the Admin dashboard for the current day.
        await loadTodayHodAttendance();


    }

    catch (error) {


        console.error(
            "Dashboard API Error:",
            error
        );

    }

}



// ============================================================
// DASHBOARD NAVIGATION
// ============================================================

function openDashboard(role) {


    switch (role) {


        case "admin":

            window.location.href =
                "admin-dashboard.html";

            break;


        case "teacher":

            window.location.href =
                "teacher-dashboard.html";

            break;


        case "hod":

            window.location.href =
                "hod-dashboard.html";

            break;


        case "student":

            window.location.href =
                "student-dashboard.html";

            break;


        case "recruiter":

            window.location.href =
                "recruiter-dashboard.html";

            break;


        default:

            console.warn(
                "Unknown dashboard role:",
                role
            );

    }

}


// ============================================================
// TODAY'S HOD FACE ATTENDANCE
// ============================================================

function getLocalDateValue() {

    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");

    return year + "-" + month + "-" + day;

}


function escapeDashboardText(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


function formatAttendanceCheckIn(value) {

    if (!value) {
        return "--";
    }

    const parsed = new Date(value);

    if (Number.isNaN(parsed.getTime())) {
        return "--";
    }

    return parsed.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });

}


function getHodAttendanceCard() {

    let card = document.getElementById(
        "todayHodAttendanceCard"
    );

    if (card) {
        return card;
    }

    card = document.createElement("section");
    card.id = "todayHodAttendanceCard";
    card.className = "card shadow-sm border-0 mt-4";
    card.style.borderRadius = "18px";
    card.style.overflow = "hidden";

    const chart = document.getElementById("attendanceChart");
    const chartSection = chart
        ? chart.closest("section, .card, .dashboard-card, .chart-card")
        : null;

    if (chartSection && chartSection.parentNode) {
        chartSection.insertAdjacentElement("afterend", card);
    } else {
        const mainArea = document.querySelector(
            "main, .main-content, .dashboard-content, .content"
        );

        (mainArea || document.body).appendChild(card);
    }

    return card;

}


async function loadTodayHodAttendance() {

    const card = getHodAttendanceCard();

    card.innerHTML =
        '<div class="p-4 text-center text-muted">' +
        '<i class="fa-solid fa-spinner fa-spin me-2"></i>' +
        "Loading today's HOD attendance..." +
        "</div>";

    try {

        const today = getLocalDateValue();

        const response = await API.request(
            "GET",
            "/faculty-attendance",
            null,
            {
                role: "hod",
                from_date: today,
                to_date: today
            }
        );

        const records = (
            response && Array.isArray(response.data)
                ? response.data
                : []
        );

        const rows = records.map(function (record) {

            const status = String(
                record.status || "present"
            ).toLowerCase();

            const badgeClass =
                status === "present"
                    ? "bg-success"
                    : status === "leave"
                        ? "bg-warning text-dark"
                        : "bg-danger";

            return (
                "<tr>" +
                    "<td>" +
                        escapeDashboardText(record.faculty_code || "--") +
                    "</td>" +
                    "<td class=\"fw-semibold\">" +
                        escapeDashboardText(record.faculty_name || "HOD") +
                    "</td>" +
                    "<td>" +
                        escapeDashboardText(record.department || "--") +
                    "</td>" +
                    "<td>" +
                        formatAttendanceCheckIn(record.created_at) +
                    "</td>" +
                    "<td>" +
                        '<span class="badge ' + badgeClass + '">' +
                            escapeDashboardText(status.toUpperCase()) +
                        "</span>" +
                    "</td>" +
                    "<td>Face Recognition</td>" +
                "</tr>"
            );

        }).join("");

        card.innerHTML =
            '<div class="card-header bg-white border-0 p-4 pb-2">' +
                '<div class="d-flex justify-content-between align-items-center gap-3 flex-wrap">' +
                    "<div>" +
                        '<h5 class="mb-1 fw-bold">' +
                            '<i class="fa-solid fa-user-check text-success me-2"></i>' +
                            "Today's HOD Attendance" +
                        "</h5>" +
                        '<small class="text-muted">' +
                            escapeDashboardText(today) +
                        "</small>" +
                    "</div>" +
                    '<span class="badge bg-primary rounded-pill">' +
                        records.length + " Marked" +
                    "</span>" +
                "</div>" +
            "</div>" +
            (
                records.length
                    ? '<div class="table-responsive p-3 pt-2">' +
                        '<table class="table table-hover align-middle mb-0">' +
                            "<thead><tr>" +
                                "<th>HOD ID</th>" +
                                "<th>Name</th>" +
                                "<th>Department</th>" +
                                "<th>Check-In</th>" +
                                "<th>Status</th>" +
                                "<th>Method</th>" +
                            "</tr></thead>" +
                            "<tbody>" + rows + "</tbody>" +
                        "</table>" +
                    "</div>"
                    : '<div class="p-4 pt-2 text-muted">' +
                        "No HOD attendance has been marked today." +
                    "</div>"
            );

    } catch (error) {

        console.error(
            "HOD attendance dashboard error:",
            error
        );

        card.innerHTML =
            '<div class="p-4 text-danger">' +
                '<i class="fa-solid fa-circle-exclamation me-2"></i>' +
                "Unable to load today's HOD attendance." +
            "</div>";

    }

}