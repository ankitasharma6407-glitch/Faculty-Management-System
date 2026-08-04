

// ===============================
// FMPS Teacher Dashboard JS
// ===============================

// Counter Animation

const counters = document.querySelectorAll(".counter");

counters.forEach(counter => {

    const updateCounter = () => {

        const target = +counter.getAttribute("data-target");
        const count = +counter.innerText;

        const increment = Math.ceil(target / 80);

        if (count < target) {

            counter.innerText = count + increment;

            setTimeout(updateCounter, 20);

        } else {

            counter.innerText = target;

        }

    };

    updateCounter();

});

// ===============================
// Dark Mode
// ===============================

const themeToggle = document.getElementById("themeToggle");

if(localStorage.getItem("theme") === "dark"){

    document.body.classList.add("dark");

    themeToggle.innerHTML='<i class="fa-solid fa-sun"></i>';

}

themeToggle.addEventListener("click",()=>{

    document.body.classList.toggle("dark");

    if(document.body.classList.contains("dark")){

        localStorage.setItem("theme","dark");

        themeToggle.innerHTML='<i class="fa-solid fa-sun"></i>';

    }else{

        localStorage.setItem("theme","light");

        themeToggle.innerHTML='<i class="fa-solid fa-moon"></i>';

    }

});

// ===============================
// Live Clock
// ===============================

function updateClock(){

    const now=new Date();

    document.getElementById("liveTime").innerHTML=
    now.toLocaleTimeString();

    document.getElementById("liveDay").innerHTML=
    now.toLocaleDateString("en-US",{weekday:"long"});

    document.getElementById("liveDate").innerHTML=
    now.toLocaleDateString("en-GB",{
        day:"numeric",
        month:"long",
        year:"numeric"
    });

}

updateClock();

setInterval(updateClock,1000);

// ===============================
// Attendance Chart
// ===============================

new Chart(document.getElementById("attendanceChart"),{

    type:"doughnut",

    data:{

        labels:["Present","Absent","Leave"],

        datasets:[{

            data:[82,12,6],

            backgroundColor:[
                "#6F42C1",
                "#DC3545",
                "#FFC107"
            ]

        }]

    },

    options:{
        responsive:true,
        plugins:{
            legend:{
                position:"bottom",
                labels:{
                    color:"#FFFFFF",
                    font:{
                        size:14,
                        weight:"bold"
                    }
                }
            }
        }
    }

});

// ===============================
// Performance Chart
// ===============================

new Chart(document.getElementById("performanceChart"),{

    type:"line",

    data:{

        labels:["Jan","Feb","Mar","Apr","May","Jun"],

        datasets:[{

            label:"Performance",

            data:[72,78,80,85,88,93],

            borderColor:"#6F42C1",

            backgroundColor:"rgba(111,66,193,.15)",

            fill:true,

            tension:.4

        }]

    },

    options:{
        responsive:true,
        plugins:{
            legend:{
                position:"bottom",
                labels:{
                    color:"#FFFFFF",
                    font:{
                        size:14,
                        weight:"bold"
                    }
                }
            }
        }
    }
});

// ===============================
// Full Calendar
// ===============================

document.addEventListener("DOMContentLoaded",function(){

    const calendarEl=document.getElementById("calendar");

    const calendar=new FullCalendar.Calendar(calendarEl,{

        initialView:"dayGridMonth",

        height:500,

        events:[

            {
                title:"Faculty Meeting",
                start:"2026-07-25"
            },

            {
                title:"Holiday",
                start:"2026-07-28"
            },

            {
                title:"Internal Exam",
                start:"2026-07-30"
            },

            {
                title:"Assignment Due",
                start:"2026-08-03"
            }

        ]

    });

    calendar.render();

});

const themeMenu=document.getElementById("themeMenu");

themeMenu.addEventListener("click",function(e){

    e.preventDefault();

    document.getElementById("themeToggle").click();

});

// ===============================
// Dashboard Search
// ===============================

const searchBox = document.getElementById("searchBox");

searchBox.addEventListener("keyup", function () {

    const value = this.value.toLowerCase();

    const cards = document.querySelectorAll(
        ".card-box, .dashboard-card, .quick-actions"
    );

    cards.forEach(card => {

        if (card.innerText.toLowerCase().includes(value)) {

            card.style.display = "";

        } else {

            card.style.display = "none";

        }

    });

});

// ==========================
// Notification Bell
// ==========================

const markAllRead = document.getElementById("markAllRead");
const notificationCount = document.getElementById("notificationCount");

if (markAllRead) {

    markAllRead.addEventListener("click", function (e) {

        e.preventDefault();

        notificationCount.innerText = "0";
        notificationCount.style.display = "none";

        const items = document.querySelectorAll(".notification-item");

        items.forEach(item => {
            item.style.opacity = "0.6";
        });

        alert("All notifications marked as read.");

    });

}

/* =========================================================
            TEACHER DASHBOARD QUICK ACTIONS
========================================================= */

document.addEventListener("DOMContentLoaded", function () {


    /* =====================================================
                    TAKE ATTENDANCE
    ===================================================== */

    const takeAttendanceBtn =
        document.getElementById("quickTakeAttendance");

    if(takeAttendanceBtn){

        takeAttendanceBtn.addEventListener(
            "click",
            function(){

                window.location.href =
                    "attendance.html";

            }
        );

    }


    /* =====================================================
                    UPLOAD NOTES
    ===================================================== */

    const uploadNotesBtn =
        document.getElementById("quickUploadNotes");

    if(uploadNotesBtn){

        uploadNotesBtn.addEventListener(
            "click",
            function(){

                window.location.href =
                    "my-classes.html";

            }
        );

    }


    /* =====================================================
                    ADD ASSIGNMENT
    ===================================================== */

    const addAssignmentBtn =
        document.getElementById("quickAddAssignment");

    if(addAssignmentBtn){

        addAssignmentBtn.addEventListener(
            "click",
            function(){

                window.location.href =
                    "assignments.html";

            }
        );

    }


    /* =====================================================
                    VIEW REPORT
    ===================================================== */

    const viewReportsBtn =
        document.getElementById("quickViewReports");

    if(viewReportsBtn){

        viewReportsBtn.addEventListener(
            "click",
            function(){

                window.location.href =
                    "attendance-report.html";

            }
        );

    }


});