document.addEventListener("DOMContentLoaded", () => {
    const menuBtn = document.getElementById("menuBtn");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const closeBtn = document.getElementById("sidebarClose");
    const mobileQuery = window.matchMedia("(max-width: 991.98px)");

    if (!menuBtn || !sidebar) return;

    const setExpanded = (value) => {
        menuBtn.setAttribute("aria-expanded", String(value));
        menuBtn.setAttribute("aria-label", value ? "Cerrar menú lateral" : "Abrir menú lateral");
    };

    const openMobileMenu = () => {
        sidebar.classList.remove("closed");
        sidebar.classList.add("active");
        overlay?.classList.add("show");
        document.body.classList.add("sidebar-open");
        setExpanded(true);
    };

    const closeMobileMenu = () => {
        sidebar.classList.remove("active");
        overlay?.classList.remove("show");
        document.body.classList.remove("sidebar-open");
        setExpanded(false);
    };

    const applyViewportState = () => {
        if (mobileQuery.matches) {
            sidebar.classList.remove("closed");
            closeMobileMenu();
        } else {
            closeMobileMenu();
            const closed = localStorage.getItem("sidebarClosed") === "1";
            sidebar.classList.toggle("closed", closed);
            setExpanded(!closed);
        }
    };

    menuBtn.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (mobileQuery.matches) {
            sidebar.classList.contains("active") ? closeMobileMenu() : openMobileMenu();
        } else {
            sidebar.classList.toggle("closed");
            const closed = sidebar.classList.contains("closed");
            localStorage.setItem("sidebarClosed", closed ? "1" : "0");
            setExpanded(!closed);
        }
    });

    closeBtn?.addEventListener("click", closeMobileMenu);
    overlay?.addEventListener("click", closeMobileMenu);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && mobileQuery.matches) closeMobileMenu();
    });

    sidebar.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            if (mobileQuery.matches) closeMobileMenu();
        });
    });

    if (typeof mobileQuery.addEventListener === "function") {
        mobileQuery.addEventListener("change", applyViewportState);
    } else {
        mobileQuery.addListener(applyViewportState);
    }

    applyViewportState();
});
