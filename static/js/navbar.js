(function () {
  var navbar = document.getElementById("siteNavbar");
  var toggle = document.getElementById("navToggle");
  var menu = document.getElementById("siteNavMenu");
  var mobileWidth = 991;

  function normalizePath(path) {
    if (!path) return "/";
    return path.replace(/\/+$/, "") || "/";
  }

  function setMenuOpen(open) {
    if (!menu || !toggle) return;
    menu.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close navigation menu" : "Open navigation menu");
  }

  function closeAllDropdowns(exceptDropdown) {
    var dropdowns = document.querySelectorAll("[data-dropdown]");
    dropdowns.forEach(function (item) {
      if (exceptDropdown && item === exceptDropdown) return;
      item.classList.remove("is-open");
      var button = item.querySelector("[data-dropdown-toggle]");
      if (button) button.setAttribute("aria-expanded", "false");
    });
  }

  function highlightActiveLinks() {
    var current = normalizePath(window.location.pathname);
    var links = document.querySelectorAll("[data-nav-link]");
    var dropdownButtons = document.querySelectorAll("[data-dropdown-toggle]");

    // Clear all active states
    dropdownButtons.forEach(function (button) {
      button.classList.remove("is-active");
    });

    links.forEach(function (link) {
      link.classList.remove("is-active");
    });

    // Find exact match first
    var exactMatch = null;
    links.forEach(function (link) {
      var href = link.getAttribute("href");
      if (!href || href.charAt(0) === "#") return;

      var url = new URL(href, window.location.origin);
      var linkPath = normalizePath(url.pathname);
      
      if (current === linkPath) {
        exactMatch = link;
      }
    });

    // If exact match found, only activate that one
    if (exactMatch) {
      exactMatch.classList.add("is-active");
      
      // Only highlight dropdown parent if the link is inside a dropdown menu
      var dropdownMenu = exactMatch.closest(".app-navbar__dropdown-menu");
      if (dropdownMenu) {
        var dropdown = dropdownMenu.closest("[data-dropdown]");
        if (dropdown) {
          var button = dropdown.querySelector("[data-dropdown-toggle]");
          if (button) button.classList.add("is-active");
        }
      }
    }
  }

  function handleScrollShadow() {
    if (!navbar) return;
    navbar.classList.toggle("is-scrolled", window.scrollY > 8);
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      var isOpen = toggle.getAttribute("aria-expanded") === "true";
      setMenuOpen(!isOpen);
    });
  }

  var dropdownButtons = document.querySelectorAll("[data-dropdown-toggle]");
  dropdownButtons.forEach(function (button) {
    button.addEventListener("click", function (event) {
      event.preventDefault();
      var dropdown = button.closest("[data-dropdown]");
      if (!dropdown) return;

      var currentlyOpen = dropdown.classList.contains("is-open");
      closeAllDropdowns(dropdown);
      dropdown.classList.toggle("is-open", !currentlyOpen);
      button.setAttribute("aria-expanded", String(!currentlyOpen));
    });
  });

  document.addEventListener("click", function (event) {
    var target = event.target;
    if (!(target instanceof HTMLElement)) return;

    if (!target.closest("[data-dropdown]")) {
      closeAllDropdowns();
    }

    if (window.innerWidth <= mobileWidth && target.closest("[data-nav-link]")) {
      setMenuOpen(false);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeAllDropdowns();
      setMenuOpen(false);
    }
  });

  window.addEventListener("resize", function () {
    if (window.innerWidth > mobileWidth) {
      setMenuOpen(false);
    }
  });

  window.addEventListener("scroll", handleScrollShadow, { passive: true });

  highlightActiveLinks();
  handleScrollShadow();
})();
