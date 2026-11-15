document.addEventListener("DOMContentLoaded", function(event) {
    // Trigger Read the Docs' search addon instead of Zensical default
    document.querySelector(".md-search").addEventListener("click", (e) => {
        e.preventDefault();
        const event = new CustomEvent("readthedocs-search-show");
        document.dispatchEvent(event);
    });
});
