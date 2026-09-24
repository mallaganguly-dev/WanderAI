// ============================================
// WANDER AI - FRONTEND JAVASCRIPT
// ============================================


// Mobile menu
function toggleMenu() {

    const nav = document.querySelector(".nav-links");

    if (!nav) return;

    if (nav.style.display === "flex") {
        nav.style.display = "none";
    } else {

        nav.style.display = "flex";

        nav.style.position = "absolute";
        nav.style.top = "75px";
        nav.style.left = "4%";
        nav.style.right = "4%";

        nav.style.flexDirection = "column";
        nav.style.gap = "20px";

        nav.style.padding = "25px";

        nav.style.borderRadius = "18px";

        nav.style.background = "rgba(7, 28, 45, 0.97)";
        nav.style.backdropFilter = "blur(15px)";
    }
}


// Set minimum date to today
const dateInput = document.querySelector('input[type="date"]');

if (dateInput) {

    const today = new Date();

    const year = today.getFullYear();

    const month = String(today.getMonth() + 1).padStart(2, "0");

    const day = String(today.getDate()).padStart(2, "0");

    dateInput.min = `${year}-${month}-${day}`;
}


// Smooth form feedback
const travelForm = document.getElementById("travelForm");

if (travelForm) {

    travelForm.addEventListener("submit", function () {

        const button = travelForm.querySelector(".planner-button");

        button.innerHTML = `
            <span>✨</span>
            Creating your itinerary...
            <span>⏳</span>
        `;

        button.style.opacity = "0.8";

    });
}


// Reveal animations
const observer = new IntersectionObserver(
    (entries) => {

        entries.forEach((entry) => {

            if (entry.isIntersecting) {

                entry.target.classList.add("visible");

            }

        });

    },
    {
        threshold: 0.15
    }
);


document.querySelectorAll(
    ".destination-card, .experience-card, .feature, .why-image"
).forEach((element) => {

    element.classList.add("reveal");

    observer.observe(element);

});
