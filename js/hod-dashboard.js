// Counter Animation

const counters = document.querySelectorAll(".counter");

counters.forEach(counter => {

    const updateCounter = () => {

        const target = +counter.getAttribute("data-target");
        const count = +counter.innerText;

        const increment = Math.ceil(target / 100);

        if (count < target) {

            counter.innerText = count + increment;

            setTimeout(updateCounter, 20);

        } else {

            counter.innerText = target;

        }

    };

    updateCounter();

});

// =====================
// Live Date & Time
// =====================

function updateClock() {

    const now = new Date();

    const liveTime = document.getElementById("liveTime");
    const liveDate = document.getElementById("liveDate");

    if (liveTime) {
        liveTime.innerHTML = now.toLocaleTimeString();
    }

    if (liveDate) {
        liveDate.innerHTML = now.toLocaleDateString("en-GB", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric"
        });
    }
}

setInterval(updateClock, 1000);
updateClock();





// ================= Attendance Chart =================

const attendanceCanvas = document.getElementById("attendanceChart");

if (attendanceCanvas && typeof Chart !== "undefined") {

    new Chart(attendanceCanvas, {
        type: "bar",
        data: {
            labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            datasets: [{
                label: "Attendance %",
                data: [95, 92, 97, 93, 96, 90],
                backgroundColor: "#6c4cff",
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

// ================= Faculty Performance =================

const performanceCanvas = document.getElementById("performanceChart");

if (performanceCanvas && typeof Chart !== "undefined") {

    new Chart(performanceCanvas, {
        type: "doughnut",
        data: {
            labels: ["Excellent", "Very Good", "Good", "Average"],
            datasets: [{
                data: [40,30,20,10],
                backgroundColor: [
                    "#6c4cff",
                    "#4CAF50",
                    "#FFC107",
                    "#F44336"
                ]
            }]
        },
        options: {
            responsive: true
        }
    });

}


// Calendar

document.addEventListener("DOMContentLoaded", function () {

    const calendarEl = document.getElementById("calendar");

    if (calendarEl && typeof FullCalendar !== "undefined") {

        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: "dayGridMonth",
            height: 400,
            events: [
                { title: "Faculty Meeting", start: "2026-07-25" },
                { title: "Internal Exam", start: "2026-07-28" },
                { title: "Workshop", start: "2026-08-05" }
            ]
        });

        calendar.render();

    }

});



// =====================
// Search
// =====================

const searchBox = document.getElementById("searchBox");

if(searchBox){

searchBox.addEventListener("keyup",function(){

const value=this.value.toLowerCase();

document.querySelectorAll(".card-box,.dashboard-card,.quick-actions").forEach(card=>{

card.style.display=
card.innerText.toLowerCase().includes(value)
? ""
: "none";

});

});

}

// =====================
// Notification
// =====================

const markAllRead=document.getElementById("markAllRead");

const notificationCount=document.getElementById("notificationCount");

if(markAllRead){

markAllRead.onclick=function(e){

e.preventDefault();

notificationCount.style.display="none";

document.querySelectorAll(".notification-item").forEach(item=>{

item.style.opacity=".6";

});

};

}




/* =========================================================
              GLOBAL DARK / LIGHT MODE
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const themeToggle = document.getElementById("themeToggle");

    /* =============================================
       LOAD SAVED THEME
    ============================================= */

    const savedTheme = localStorage.getItem("hodTheme");

    if (savedTheme === "dark") {

        document.body.classList.add("dark");

    } else {

        document.body.classList.remove("dark");

    }


    /* =============================================
       UPDATE ICON
    ============================================= */

    function updateThemeIcon() {

        if (!themeToggle) return;

        const icon = themeToggle.querySelector("i");

        if (!icon) return;

        if (document.body.classList.contains("dark")) {

            icon.classList.remove("fa-moon");
            icon.classList.add("fa-sun");

            themeToggle.title = "Switch to Light Mode";

        } else {

            icon.classList.remove("fa-sun");
            icon.classList.add("fa-moon");

            themeToggle.title = "Switch to Dark Mode";

        }

    }


    updateThemeIcon();


    /* =============================================
       THEME TOGGLE
    ============================================= */

    if (themeToggle) {

        themeToggle.addEventListener("click", function () {

            document.body.classList.toggle("dark");

            if (document.body.classList.contains("dark")) {

                localStorage.setItem("hodTheme", "dark");

            } else {

                localStorage.setItem("hodTheme", "light");

            }

            updateThemeIcon();

        });

    }

});