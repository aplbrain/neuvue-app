(function () {
  function slugify(text, index) {
    var slug = text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");

    return slug || "section-" + index;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var content = document.querySelector(".js-doc-content");
    var toc = document.getElementById("docToc");

    if (!content || !toc) {
      return;
    }

    var headers = Array.prototype.slice.call(content.querySelectorAll("h1, h2, h3"));

    if (!headers.length) {
      toc.innerHTML = '<div class="nv-empty">No sections found.</div>';
      return;
    }

    var indexButton = document.createElement("button");
    indexButton.type = "button";
    indexButton.className = "nv-toc-button";
    indexButton.textContent = "Index";
    indexButton.addEventListener("click", function () {
      content.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    toc.appendChild(indexButton);

    headers.forEach(function (header, index) {
      if (!header.id) {
        header.id = slugify(header.textContent, index);
      }

      var button = document.createElement("button");
      button.type = "button";
      button.className = "nv-toc-button nv-toc-" + header.localName;
      button.textContent = header.textContent;
      button.addEventListener("click", function () {
        header.scrollIntoView({ behavior: "smooth", block: "start" });
      });

      toc.appendChild(button);
    });
  });
})();
