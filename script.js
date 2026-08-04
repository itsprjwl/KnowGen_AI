const topBtn = document.getElementById("topBtn");
const themeBtn = document.getElementById("themeToggle");
const loader = document.getElementById("loader");

function toggleTopButton() {
    if (!topBtn) return;
    const scrollY = window.scrollY || document.documentElement.scrollTop;
    topBtn.style.display = scrollY > 300 ? "block" : "none";
}

if (topBtn) {
    window.addEventListener("scroll", toggleTopButton);
    topBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
}

const hiddenElements = document.querySelectorAll("section");
if (typeof IntersectionObserver !== "undefined") {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("show");
                entry.target.classList.remove("hidden");
            }
        });
    }, { threshold: 0.15 });

    hiddenElements.forEach((el) => {
        el.classList.add("hidden");
        observer.observe(el);
    });
} else {
    hiddenElements.forEach((el) => el.classList.add("show"));
}

window.addEventListener("load", () => {
    if (document.body) {
        document.body.classList.add("light");
    }
    if (themeBtn) {
        themeBtn.textContent = "🌙";
    }
    setTimeout(() => {
        if (loader) loader.style.display = "none";
        toggleTopButton();
    }, 500);
});

if (themeBtn) {
    themeBtn.addEventListener("click", () => {
        document.body.classList.toggle("light");
        const isLight = document.body.classList.contains("light");
        themeBtn.textContent = isLight ? "🌙" : "☀️";
    });
}
