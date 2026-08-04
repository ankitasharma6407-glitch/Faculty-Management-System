document.addEventListener("DOMContentLoaded", function () {

    /* ================= Elements ================= */

    const themeToggle = document.getElementById("themeToggle");
    const themeMenu = document.getElementById("themeMenu");

    const profileBtn = document.getElementById("profileBtn");
    const profileDropdown = document.getElementById("profileDropdown");

    const greeting = document.getElementById("greeting");

    const searchBox = document.getElementById("searchBox");

    const markAllRead = document.getElementById("markAllRead");
    const notificationCount = document.getElementById("notificationCount");

    /* ================= Greeting ================= */

    if (greeting) {

        const hour = new Date().getHours();

        if (hour < 12) {
            greeting.innerHTML = "Good Morning ☀️";
        }
        else if (hour < 17) {
            greeting.innerHTML = "Good Afternoon 🌤️";
        }
        else {
            greeting.innerHTML = "Good Evening 🌙";
        }

    }

    /* ================= Dark Mode ================= */

    if (localStorage.getItem("theme") === "dark") {

        document.body.classList.add("dark");

        if (themeToggle) {
            themeToggle.innerHTML =
                '<i class="fa-solid fa-sun"></i>';
        }

    }

    if (themeToggle) {

        themeToggle.addEventListener("click", function () {

            document.body.classList.toggle("dark");

            if (document.body.classList.contains("dark")) {

                localStorage.setItem("theme", "dark");

                themeToggle.innerHTML =
                    '<i class="fa-solid fa-sun"></i>';

            } else {

                localStorage.setItem("theme", "light");

                themeToggle.innerHTML =
                    '<i class="fa-solid fa-moon"></i>';

            }

        });

    }

    if (themeMenu) {

        themeMenu.addEventListener("click", function (e) {

            e.preventDefault();

            themeToggle.click();

        });

    }

    /* ================= Profile Dropdown ================= */

    if (profileBtn) {

        profileBtn.addEventListener("click", function (e) {

            e.stopPropagation();

            profileDropdown.classList.toggle("show");

        });

    }

    document.addEventListener("click", function () {

        if (profileDropdown) {

            profileDropdown.classList.remove("show");

        }

    });

    /* ================= Search ================= */

    if (searchBox) {

        searchBox.addEventListener("keyup", function () {

            const value = this.value.toLowerCase();

            document.querySelectorAll(

                ".stat-card,.quick-card,.chart-card,.calendar-card,.activity-card,.table-card,.notification-panel"

            ).forEach(function (card) {

                card.style.display =

                    card.innerText.toLowerCase().includes(value)

                        ? ""

                        : "none";

            });

        });

    }

    /* ================= Notifications ================= */

    if (markAllRead) {

        markAllRead.addEventListener("click", function (e) {

            e.preventDefault();

            if (notificationCount) {

                notificationCount.style.display = "none";

            }

        });

    }

    /* ================= Attendance Chart ================= */

    const attendance = document.getElementById("attendanceChart");

    if (attendance) {

        new Chart(attendance, {

            type: "bar",

            data: {

                labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],

                datasets: [{

                    label: "Attendance %",

                    data: [92, 95, 91, 96, 94, 98],

                    backgroundColor: [

                        "#6b3dff",
                        "#7b4cff",
                        "#8b5cff",
                        "#9b6cff",
                        "#ab7cff",
                        "#bb8cff"

                    ],

                    borderRadius: 8

                }]

            },

            options: {

                responsive: true,

                plugins: {

                    legend: {

                        display: false

                    }

                }

            }

        });

    }

    /* ================= Performance Chart ================= */

    const performance = document.getElementById("performanceChart");

    if (performance) {

        new Chart(performance, {

            type: "doughnut",

            data: {

                labels: [

                    "Excellent",
                    "Good",
                    "Average",
                    "Poor"

                ],

                datasets: [{

                    data: [45, 30, 15, 10],

                    backgroundColor: [

                        "#6b3dff",
                        "#0d6efd",
                        "#ffc107",
                        "#dc3545"

                    ]

                }]

            },

            options: {

                responsive: true,

                plugins: {

                    legend: {

                        position: "bottom"

                    }

                }

            }

        });

    }

    /* ================= Calendar ================= */

    const calendarEl = document.getElementById("calendar");

    if (calendarEl) {

        const calendar = new FullCalendar.Calendar(calendarEl, {

            initialView: "dayGridMonth",

            height: 500,

            events: [

                {

                    title: "Faculty Meeting",

                    start: "2026-07-25"

                },

                {

                    title: "Placement Drive",

                    start: "2026-07-28"

                },

                {

                    title: "Internal Exam",

                    start: "2026-07-30"

                }

            ]

        });

        calendar.render();

    }

    /* ================= Notification Popup ================= */

    document.querySelectorAll(".notification-item").forEach(function (item) {

        item.addEventListener("click", function () {

            alert(item.innerText);

        });

    });

    /* ================= Logout ================= */

    document.querySelectorAll(".logout-btn,.logout-link").forEach(function (btn) {

        btn.addEventListener("click", function (e) {

            if (!confirm("Do you really want to logout?")) {

                e.preventDefault();

            }

        });

    });

});

/* ================= Dashboard Navigation ================= */

function openDashboard(role) {

    switch (role) {

        case "admin":

            window.location.href = "admin-dashboard.html";

            break;

        case "teacher":

            window.location.href = "teacher-dashboard.html";

            break;

        case "hod":

            window.location.href = "hod-dashboard.html";

            break;

        case "student":

            window.location.href = "student-dashboard.html";

            break;

        case "recruiter":

            window.location.href = "recruiter-dashboard.html";

            break;

    }

}

// ==============================
// Change Profile Photo
// ==============================

const changePhoto = document.getElementById("changePhoto");

if (changePhoto) {
    changePhoto.addEventListener("click", function(e){
        e.preventDefault();
        alert("Profile photo upload feature will be available after backend integration.");
    });
}
