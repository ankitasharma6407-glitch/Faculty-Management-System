// ===============================
// Sticky Navbar
// ===============================

window.addEventListener("scroll", function () {

    const navbar = document.querySelector(".custom-navbar");

    if (window.scrollY > 50) {

        navbar.style.padding = "10px 0";
        navbar.style.boxShadow = "0 10px 30px rgba(0,0,0,0.15)";

    } else {

        navbar.style.padding = "14px 0";
        navbar.style.boxShadow = "0 8px 25px rgba(0,0,0,0.08)";

    }

});

// ===============================
// Smooth Scrolling
// ===============================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {

    anchor.addEventListener("click", function (e) {

        e.preventDefault();

        const target = document.querySelector(this.getAttribute("href"));

        if (target) {

            target.scrollIntoView({

                behavior: "smooth"

            });

        }

    });

});

// ===============================
// Active Navbar Link
// ===============================

const sections = document.querySelectorAll("section");
const navLinks = document.querySelectorAll(".nav-link");

window.addEventListener("scroll", () => {

    let current = "";

    sections.forEach(section => {

        const sectionTop = section.offsetTop - 120;

        if (pageYOffset >= sectionTop) {

            current = section.getAttribute("id");

        }

    });

    navLinks.forEach(link => {

        link.classList.remove("active");

        if (link.getAttribute("href") === "#" + current) {

            link.classList.add("active");

        }

    });

});

// ===============================
// Counter Animation
// ===============================

const counters = document.querySelectorAll(".stat-box h2");

let started = false;

window.addEventListener("scroll", () => {

    const stats = document.querySelector(".stats-section");

    if (!stats) return;

    const trigger = stats.offsetTop - 300;

    if (window.scrollY > trigger && !started) {

        started = true;

        counters.forEach(counter => {

            const text = counter.innerText;

            const number = parseInt(text.replace(/\D/g, ""));

            if (isNaN(number)) return;

            let count = 0;

            const speed = number / 80;

            const update = () => {

                count += speed;

                if (count < number) {

                    counter.innerText = Math.floor(count) + "+";

                    requestAnimationFrame(update);

                } else {

                    counter.innerText = text;

                }

            };

            update();

        });

    }

});

// ===============================
// Fade In Animation
// ===============================

const observer = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if (entry.isIntersecting) {

            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0)";

        }

    });

}, {

    threshold: 0.2

});

document.querySelectorAll(".feature-card, .about-card, .timeline-item, .contact-card").forEach(el => {

    el.style.opacity = "0";
    el.style.transform = "translateY(40px)";
    el.style.transition = "0.8s ease";

    observer.observe(el);

});

// ===============================
// Contact Form
// ===============================

const form = document.querySelector(".contact-form form");

if (form) {

    form.addEventListener("submit", function (e) {

        e.preventDefault();

        alert("Thank you! Your message has been sent successfully.");

        form.reset();

    });

}

// =========================
// DARK / LIGHT MODE
// =========================

const themeToggle = document.getElementById("themeToggle");

// Load saved theme
if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark");
    themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
} else {
    themeToggle.innerHTML = '<i class="fa-solid fa-moon"></i>';
}

// Toggle Theme


// ============================================================
// GLOBAL INDEX THEME
// ============================================================

(function () {

    const themeToggle =
        document.getElementById("themeToggle");

    if (!themeToggle) {
        return;
    }

    function applyIndexTheme() {

        const theme =
            localStorage.getItem("theme") || "light";

        document.body.classList.toggle(
            "dark",
            theme === "dark"
        );

        const icon =
            themeToggle.querySelector("i");

        if (icon) {
            icon.className =
                theme === "dark"
                    ? "fa-solid fa-sun"
                    : "fa-solid fa-moon";
        }
    }


    themeToggle.addEventListener(
        "click",
        function () {

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

            applyIndexTheme();
        }
    );


    // Apply theme when page opens
    applyIndexTheme();


    // Useful when returning with Back button
    window.addEventListener(
        "pageshow",
        applyIndexTheme
    );


    // Sync if another tab changes theme
    window.addEventListener(
        "storage",
        function (event) {

            if (event.key === "theme") {
                applyIndexTheme();
            }
        }
    );

})();