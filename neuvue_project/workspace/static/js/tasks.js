(function () {
  function initTooltips() {
    if (!window.bootstrap) {
      return;
    }

    var tooltipTriggerList = Array.prototype.slice.call(
      document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
      new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  function initPanels() {
    document.querySelectorAll(".js-task-panel-toggle").forEach(function (button) {
      button.addEventListener("click", function () {
        var target = document.getElementById(button.dataset.target);
        if (!target) {
          return;
        }

        var isExpanded = button.getAttribute("aria-expanded") === "true";
        button.setAttribute("aria-expanded", String(!isExpanded));
        target.hidden = isExpanded;
      });
    });
  }

  function initTabs() {
    document.querySelectorAll("[data-task-card]").forEach(function (card) {
      card.querySelectorAll(".js-task-tab").forEach(function (tab) {
        tab.addEventListener("click", function () {
          card.querySelectorAll(".js-task-tab").forEach(function (otherTab) {
            otherTab.classList.remove("active");
            otherTab.setAttribute("aria-selected", "false");
          });

          card.querySelectorAll(".nv-tab-panel").forEach(function (panel) {
            panel.hidden = true;
          });

          tab.classList.add("active");
          tab.setAttribute("aria-selected", "true");

          var target = document.getElementById(tab.dataset.target);
          if (target) {
            target.hidden = false;
          }
        });
      });
    });
  }

  function initLoadingLinks() {
    document.querySelectorAll(".js-loading-link").forEach(function (link) {
      link.addEventListener("click", function () {
        if (link.dataset.spinnerTarget && window.triggerLoadingSpinner) {
          triggerLoadingSpinner(link.dataset.spinnerTarget);
        }
      });
    });
  }

  function initNamespaceSort() {
    var sortSelect = document.getElementById("namespaceSort");
    var namespaceCards = Array.prototype.slice.call(
      document.querySelectorAll("[data-namespace-card]")
    );

    if (!sortSelect || !namespaceCards.length) {
      return;
    }

    function sortedCards(sortValue) {
      return namespaceCards.slice().sort(function (a, b) {
        if (sortValue === "name-asc") {
          return (a.dataset.name || "").localeCompare(b.dataset.name || "");
        }

        if (sortValue === "activity-desc") {
          return Number(b.dataset.lastActivity || 0) - Number(a.dataset.lastActivity || 0);
        }

        return Number(b.dataset.pending || 0) - Number(a.dataset.pending || 0);
      });
    }

    function applySort() {
      sortedCards(sortSelect.value).forEach(function (card, index) {
        card.style.setProperty("--nv-sort-order", index + 1);
      });
    }

    sortSelect.addEventListener("change", applySort);
    applySort();
  }

  function triggerToast(toastText) {
    var toastBody = document.getElementById("toast-body");
    var toastDiv = document.getElementById("toast");

    if (!toastBody || !toastDiv || !window.bootstrap) {
      return;
    }

    toastBody.textContent = toastText;
    new bootstrap.Toast(toastDiv).show();
  }

  function resetSpinner(spinnerId, originalText) {
    if (spinnerId && window.removeLoadingSpinner) {
      removeLoadingSpinner(spinnerId, originalText);
    }
  }

  function postQueueAction(namespace, options) {
    var csrftoken = window.getCookie ? getCookie("csrftoken") : "";
    var formData = new FormData();
    formData.append("namespace", namespace);

    if (options.reassign) {
      formData.append("reassignTasks", "True");
    }

    if (options.spinnerId && window.triggerLoadingSpinner) {
      triggerLoadingSpinner(options.spinnerId);
    }

    fetch("", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
      },
      body: formData,
      credentials: "same-origin",
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Queue request failed");
        }
        return response.text();
      })
      .then(function (text) {
        if (text) {
          triggerToast(text);
          resetSpinner(options.spinnerId, options.originalText);
          if (options.reloadAfterMessage) {
            window.setTimeout(function () {
              window.location.reload();
            }, 900);
          }
          return;
        }

        window.location.reload();
      })
      .catch(function () {
        triggerToast("Unable to reach queue. Please try again.");
        resetSpinner(options.spinnerId, options.originalText);
      });
  }

  function copyActionData(source, target) {
    target.dataset.namespace = source.dataset.namespace || "";
    target.dataset.spinnerTarget = source.dataset.spinnerTarget || "";
  }

  function initModals() {
    var addModal = document.getElementById("confirmAddTasksModal");
    var reassignModal = document.getElementById("confirmReassignTasksModal");
    var addConfirm = document.querySelector(".js-confirm-add-tasks");
    var reassignConfirm = document.querySelector(".js-confirm-reassign-tasks");

    if (addModal && addConfirm) {
      addModal.addEventListener("show.bs.modal", function (event) {
        var source = event.relatedTarget;
        if (!source) {
          return;
        }

        var displayName = source.dataset.displayName || "this queue";
        addModal.querySelector(".modal-title").textContent = "Add more " + displayName + " tasks?";
        copyActionData(source, addConfirm);
      });

      addConfirm.addEventListener("click", function () {
        postQueueAction(addConfirm.dataset.namespace, {
          spinnerId: addConfirm.dataset.spinnerTarget,
          originalText: "Add More Tasks",
          reloadAfterMessage: false,
          reassign: false,
        });
      });
    }

    if (reassignModal && reassignConfirm) {
      reassignModal.addEventListener("show.bs.modal", function (event) {
        var source = event.relatedTarget;
        if (!source) {
          return;
        }

        var displayName = source.dataset.displayName || "this queue";
        reassignModal.querySelector(".modal-title").textContent =
          "Reassign all skipped " + displayName + " tasks?";
        copyActionData(source, reassignConfirm);
      });

      reassignConfirm.addEventListener("click", function () {
        postQueueAction(reassignConfirm.dataset.namespace, {
          spinnerId: reassignConfirm.dataset.spinnerTarget,
          originalText: "Remove Skipped Tasks",
          reloadAfterMessage: true,
          reassign: true,
        });
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTooltips();
    initPanels();
    initTabs();
    initLoadingLinks();
    initNamespaceSort();
    initModals();
  });
})();
