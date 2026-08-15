"use strict";


/* ============================================================
   HOD DASHBOARD INITIALIZATION
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
        Load REAL department data before
        counter animation starts.
        */

        await loadHodDashboardData();


        setupCounters();

        setupClock();

        setupAttendanceChart();

        setupPerformanceChart();

        setupTeacherOverviewChart();

        setupCalendar();

        setupSearch();

        setupNotifications();

        setupTheme();

        setupLogout();

    }
);



/* ============================================================
   HOD AUTHENTICATION
============================================================ */

async function protectHodDashboard() {


    const token =
        localStorage.getItem(
            "fmps_access_token"
        );


    /* No token */

    if (!token) {

        window.location.replace(
            "hod-login.html"
        );

        return false;

    }


    /* API client check */

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


        /*
        Verify JWT from backend.
        */

        const response =
            await API.auth.me();


        console.log(
            "HOD Authentication:",
            response
        );


        let user = null;


        /*
        Support different API response structures.
        */

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


        /* User check */

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


        /* Role check */

        const role =
            String(
                user.role || ""
            )
                .trim()
                .toLowerCase();


        if (
            role !== "hod"
        ) {

            API.auth.logout();


            alert(
                "Access denied. HOD account required."
            );


            window.location.replace(
                "hod-login.html"
            );


            return false;

        }


        /* Active account check */

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


        /*
        Keep current user stored.
        */

        if (API.store) {

            API.store.user =
                user;

        }

        else {

            localStorage.setItem(
                "fmps_user",
                JSON.stringify(user)
            );

        }


        displayLoggedInHod(
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
   DISPLAY LOGGED-IN HOD
============================================================ */

function displayLoggedInHod(
    user
) {


    const profile =
        user.profile || {};


    const hodName =

        profile.full_name ||

        user.username ||

        user.email ||

        "HOD";


    /* Top navbar name */

    const profileName =
        document.querySelector(
            ".profile span"
        );


    if (profileName) {

        profileName.textContent =
            "Welcome, " + hodName;

    }


    /* Welcome banner */

    const welcomeHeading =
        document.getElementById(
            "hodWelcomeHeading"
        );


    if (welcomeHeading) {

        welcomeHeading.textContent =
            "Welcome Back, " +
            hodName +
            " 👋";

    }


    /* Profile image */

    const profileImage =
        document.querySelector(
            ".profile img"
        );


    const photoUrl =

        profile.photo_url ||

        profile.image_url ||

        profile.photo ||

        null;


    if (
        profileImage &&
        photoUrl
    ) {


        if (
            String(photoUrl)
                .startsWith("http")
        ) {

            profileImage.src =
                photoUrl;

        }

        else {

            profileImage.src =
                "http://127.0.0.1:5000" +
                photoUrl;

        }

    }

}



/* ============================================================
   LOAD REAL HOD DASHBOARD DATA
============================================================ */

async function loadHodDashboardData() {


    try {


        const response =
            await API.request(
                "GET",
                "/hods/dashboard"
            );


        console.log(
            "Real HOD Dashboard Data:",
            response
        );


        if (
            !response ||
            !response.success ||
            !response.data
        ) {

            console.error(
                "Invalid HOD dashboard response."
            );

            return;

        }


        const data =
            response.data;


        /*
        --------------------------------------------------------
        REAL TEACHER COUNT
        --------------------------------------------------------
        */

        setCounterTarget(
            "hodTotalTeachers",
            data.total_teachers
        );


        /*
        --------------------------------------------------------
        REAL STUDENT COUNT
        --------------------------------------------------------
        */

        setCounterTarget(
            "hodTotalStudents",
            data.total_students
        );


        /*
        --------------------------------------------------------
        HOD manages one assigned department.
        --------------------------------------------------------
        */

        setCounterTarget(
            "hodTotalDepartments",
            data.total_departments
        );


        /*
        --------------------------------------------------------
        Leave API not connected yet.
        Do not show fake 12.
        --------------------------------------------------------
        */

        setCounterTarget(
            "hodPendingRequests",
            0
        );


        /*
        --------------------------------------------------------
        Department name in welcome message.
        --------------------------------------------------------
        */

        const welcomeDescription =
            document.getElementById(
                "hodWelcomeDescription"
            );


        if (
            welcomeDescription &&
            data.department
        ) {

            welcomeDescription.textContent =

                "Manage teachers, monitor attendance, " +

                "approve leave requests, publish notices, " +

                "track performance and generate reports for " +

                data.department +

                " Department.";

        }


        /*
        Store current HOD dashboard data.

        Later department teacher/attendance APIs
        can use this information.
        */

        window.currentHodDashboardData =
            data;


        console.log(
            "Current Department:",
            data.department
        );


        console.log(
            "Department ID:",
            data.department_id
        );


        console.log(
            "Teachers:",
            data.total_teachers
        );


        console.log(
            "Students:",
            data.total_students
        );


    }

    catch (error) {


        console.error(
            "HOD Dashboard Data Error:",
            error
        );

    }

}



/* ============================================================
   SET COUNTER TARGET
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

        console.warn(
            "Counter element not found:",
            elementId
        );

        return;

    }


    const number =
        Number(
            value
        );


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


            if (
                target <= 0
            ) {

                counter.textContent =
                    "0";

                return;

            }


            let count =
                0;


            const increment =
                Math.max(
                    1,
                    Math.ceil(
                        target / 100
                    )
                );


            function updateCounter() {


                count +=
                    increment;


                if (
                    count < target
                ) {

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
   LIVE DATE AND TIME
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
                now.toLocaleTimeString();

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
   ATTENDANCE CHART
============================================================ */

function setupAttendanceChart() {


    const attendanceCanvas =
        document.getElementById(
            "attendanceChart"
        );


    if (
        !attendanceCanvas ||
        typeof Chart === "undefined"
    ) {

        return;

    }


    new Chart(
        attendanceCanvas,
        {

            type:
                "bar",

            data: {

                labels: [

                    "Mon",

                    "Tue",

                    "Wed",

                    "Thu",

                    "Fri",

                    "Sat"

                ],

                datasets: [

                    {

                        label:
                            "Attendance %",

                        data: [

                            95,

                            92,

                            97,

                            93,

                            96,

                            90

                        ],

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

                plugins: {

                    legend: {

                        display:
                            false

                    }

                }

            }

        }
    );

}



/* ============================================================
   FACULTY PERFORMANCE CHART
============================================================ */

function setupPerformanceChart() {


    const performanceCanvas =
        document.getElementById(
            "performanceChart"
        );


    if (
        !performanceCanvas ||
        typeof Chart === "undefined"
    ) {

        return;

    }


    new Chart(
        performanceCanvas,
        {

            type:
                "doughnut",

            data: {

                labels: [

                    "Excellent",

                    "Very Good",

                    "Good",

                    "Average"

                ],

                datasets: [

                    {

                        data: [

                            40,

                            30,

                            20,

                            10

                        ],

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
                    true

            }

        }
    );

}



/* ============================================================
   TEACHER OVERVIEW CHART
============================================================ */

function setupTeacherOverviewChart() {


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


    const dashboard =
        window.currentHodDashboardData || {};


    const teachers =
        Number(
            dashboard.total_teachers
        ) || 0;


    new Chart(
        canvas,
        {

            type:
                "doughnut",

            data: {

                labels: [
                    "Teachers"
                ],

                datasets: [

                    {

                        data: [
                            teachers
                        ],

                        backgroundColor: [
                            "#6c4cff"
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
   CALENDAR
============================================================ */

function setupCalendar() {


    const calendarEl =
        document.getElementById(
            "calendar"
        );


    if (
        !calendarEl ||
        typeof FullCalendar === "undefined"
    ) {

        return;

    }


    const calendar =
        new FullCalendar.Calendar(
            calendarEl,
            {

                initialView:
                    "dayGridMonth",

                height:
                    400,

                events: [

                    {

                        title:
                            "Faculty Meeting",

                        start:
                            "2026-07-25"

                    },

                    {

                        title:
                            "Internal Exam",

                        start:
                            "2026-07-28"

                    },

                    {

                        title:
                            "Workshop",

                        start:
                            "2026-08-05"

                    }

                ]

            }
        );


    calendar.render();

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
                    ".card-box, .dashboard-card, .quick-actions"
                )
                .forEach(
                    function (card) {


                        const cardText =
                            card.innerText
                                .toLowerCase();


                        card.style.display =
                            cardText.includes(
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
   NOTIFICATIONS
============================================================ */

function setupNotifications() {


    const markAllRead =
        document.getElementById(
            "markAllRead"
        );


    const notificationCount =
        document.getElementById(
            "notificationCount"
        );


    if (!markAllRead) {

        return;

    }


    markAllRead.addEventListener(
        "click",
        function (event) {


            event.preventDefault();


            if (
                notificationCount
            ) {

                notificationCount.style.display =
                    "none";

            }


            document
                .querySelectorAll(
                    ".notification-item"
                )
                .forEach(
                    function (item) {

                        item.style.opacity =
                            "0.6";

                    }
                );

        }
    );

}



/* ============================================================
   DARK / LIGHT MODE
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


    if (
        savedTheme === "dark"
    ) {

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


    if (themeToggle) {


        themeToggle.addEventListener(
            "click",
            function () {


                document.body.classList
                    .toggle(
                        "dark"
                    );


                if (
                    document.body.classList
                        .contains(
                            "dark"
                        )
                ) {

                    localStorage.setItem(
                        "hodTheme",
                        "dark"
                    );

                }

                else {

                    localStorage.setItem(
                        "hodTheme",
                        "light"
                    );

                }


                updateThemeIcon();

            }
        );

    }

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