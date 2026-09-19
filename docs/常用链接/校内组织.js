(function () {
  "use strict";

  function legacyCopy(text) {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand("copy");
    } catch (error) {}
    document.body.removeChild(area);
  }

  document.querySelectorAll(".flip-card").forEach(function (card) {
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-pressed", "false");

    function toggle() {
      const flipped = card.classList.toggle("flipped");
      card.setAttribute("aria-pressed", flipped ? "true" : "false");
    }

    card.addEventListener("click", function (event) {
      if (event.target.closest(".bk-link, .bk-copy")) {
        return;
      }
      toggle();
    });
    card.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle();
      }
    });
  });

  document.querySelectorAll(".bk-copy").forEach(function (element) {
    element.addEventListener("click", function (event) {
      event.stopPropagation();
      const value = element.getAttribute("data-copy") || "";
      const valueElement = element.querySelector(".bk-copy-val");

      function done() {
        if (!valueElement) {
          return;
        }
        element.classList.add("copied");
        valueElement.textContent = "已复制 ✓";
        clearTimeout(element._copyTimer);
        element._copyTimer = setTimeout(function () {
          valueElement.textContent = value;
          element.classList.remove("copied");
        }, 1200);
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value).then(done).catch(function () {
          legacyCopy(value);
          done();
        });
      } else {
        legacyCopy(value);
        done();
      }
    });
  });
})();
