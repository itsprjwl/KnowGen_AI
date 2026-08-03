const topBtn = document.getElementById("topBtn");

window.onscroll = function () {
    if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
        topBtn.style.display = "block";
    } else {
        topBtn.style.display = "none";
    }
};

topBtn.onclick = function () {
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
};

const hiddenElements = document.querySelectorAll("section");

const observer = new IntersectionObserver((entries)=>{
    entries.forEach((entry)=>{
        if(entry.isIntersecting){
            entry.target.classList.add("show");
        }
    });
});

hiddenElements.forEach((el)=>{
    el.classList.add("hidden");
    observer.observe(el);
});

window.addEventListener("load", function () {
    document.getElementById("loader").style.display = "none";
});

const themeBtn = document.getElementById("themeToggle");

themeBtn.onclick = function(){

    document.body.classList.toggle("dark");

}