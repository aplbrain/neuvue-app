(function () {
  const configElement = document.getElementById("inspect-config");
  const config = configElement ? JSON.parse(configElement.textContent) : {};

  function setPanel(open) {
    const sidemenu = document.getElementById("neuVue-sidemenu");
    const sidebar = document.getElementById("neuVue-sidebar");
    const sidecontent = document.getElementById("neuVue-sidecontent");
    const neuroglancerWindow = document.getElementById("neuroglancer");

    if (!sidemenu || !sidebar || !sidecontent) {
      return;
    }

    sidemenu.style.width = open ? "330px" : "42px";
    sidebar.style.width = "42px";
    sidecontent.style.width = open ? "calc(100% - 42px)" : "0";
    sidecontent.style.visibility = open ? "visible" : "hidden";

    document.querySelectorAll(".instructionBox").forEach((sideBox) => {
      sideBox.style.visibility = open ? "visible" : "hidden";
    });

    if (neuroglancerWindow) {
      neuroglancerWindow.style.width = open
        ? "calc(100% - 330px)"
        : "calc(100% - 42px)";
      neuroglancerWindow.style.left = "0";
    }
  }

  function openSideMenu() {
    setPanel(true);
  }

  function closeSideMenu() {
    setPanel(false);
  }

  function sidemenuContent() {
    const sidecontent = document.getElementById("neuVue-sidecontent");
    const isOpen = sidecontent && sidecontent.style.visibility !== "hidden";

    if (isOpen) {
      closeSideMenu();
      window.localStorage.setItem("sidebarStatus", "closed");
    } else {
      openSideMenu();
      window.localStorage.setItem("sidebarStatus", "open");
    }
  }

  function triggerToast(toastText) {
    const toastBody = document.getElementById("toast-body");
    const toastDiv = document.getElementById("toast");

    if (!toastBody || !toastDiv || !window.bootstrap) {
      return;
    }

    toastBody.textContent = toastText;
    new bootstrap.Toast(toastDiv).show();
  }

  function normalizeNgState(state) {
    if (typeof state !== "string") {
      return state;
    }

    try {
      const parsedState = JSON.parse(state);
      if (
        parsedState &&
        typeof parsedState === "object" &&
        Object.prototype.hasOwnProperty.call(parsedState, "value")
      ) {
        return parsedState.value;
      }
      return parsedState;
    } catch (error) {
      return state;
    }
  }

  function tryRestoreState() {
    if (!config.ngState || config.ngUrl) {
      return;
    }

    if (typeof viewer !== "undefined") {
      try {
        viewer.state.restoreState(normalizeNgState(config.ngState));
        console.log("Viewer state restored successfully.");
      } catch (error) {
        console.error("Error restoring viewer state:", error);
      }
      return;
    }

    setTimeout(tryRestoreState, 100);
  }

  function getLink() {
    if (config.ngHost === "neuvue" && typeof viewer !== "undefined") {
      viewer.postJsonState(true, undefined, true, function () {
        const urlPrefix = "https://neuroglancer.neuvue.io/?json_url=";
        copyToClipboard(urlPrefix.concat(viewer.saver.savedUrl));
        triggerToast("Copied link to clipboard");
      });
      return;
    }

    if (config.ngHost === "spelunker" && typeof viewer !== "undefined") {
      const urlPrefix = "https://spelunker.cave-explorer.org/#!";
      copyToClipboard(urlPrefix.concat(JSON.stringify(viewer.state.toJSON())));
      triggerToast("Copied link to clipboard");
      return;
    }

    triggerToast("Copy Link unavailable on embedded Neuroglancer task type");
  }

  function initCopyButtons() {
    document.querySelectorAll("[data-copy-value]").forEach((button) => {
      button.addEventListener("click", function () {
        copyToClipboard(button.dataset.copyValue || "");
        triggerToast("Copied to clipboard");
      });
    });
  }

  function initSidebar() {
    if (!config.taskId) {
      return;
    }

    if (window.localStorage.getItem("sidebarStatus") === "closed") {
      closeSideMenu();
    } else {
      openSideMenu();
    }
  }

  function initActions() {
    const copyNgLinkButton = document.getElementById("btnCopyNgLink");
    if (copyNgLinkButton) {
      copyNgLinkButton.addEventListener("click", getLink);
    }

    document.querySelectorAll("[data-exit-url]").forEach((button) => {
      button.addEventListener("click", function () {
        document.location =
          button.dataset.exitUrl || (config.urls && config.urls.inspect) || "/inspect/";
      });
    });

    const lookupForm = document.getElementById("inspectLookupForm");
    if (lookupForm) {
      lookupForm.addEventListener("submit", function () {
        triggerLoadingSpinner("submit-spinner");
      });
    }
  }

  window.openSideMenu = openSideMenu;
  window.closeSideMenu = closeSideMenu;
  window.sidemenu_content = sidemenuContent;
  window.getLink = getLink;
  window.triggerToast = triggerToast;

  document.addEventListener("DOMContentLoaded", function () {
    initSidebar();
    initCopyButtons();
    initActions();
    tryRestoreState();
  });

  window.addEventListener("pageshow", function () {
    if (document.getElementById("submit-spinner") !== null) {
      removeLoadingSpinner("submit-spinner", "Submit");
    }
  });
})();
