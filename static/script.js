document.addEventListener("DOMContentLoaded", function() {
    const modal = document.getElementById("popupForm");
    const btn = document.getElementById("openFormBtn");
    const span = document.getElementById("closeBtn");

    btn.addEventListener("click", () => modal.style.display = "block");
    span.addEventListener("click", () => modal.style.display = "none");
    window.addEventListener("click", (event) => {
        if(event.target == modal) modal.style.display = "none";
    });
});
