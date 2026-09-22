(function () {
  const configElement = document.getElementById("cell-viewer-config");
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
      return JSON.parse(state);
    } catch (error) {
      return state;
    }
  }

  function tryRestoreState() {
    if (!config.ngState) {
      return;
    }

    if (typeof viewer !== "undefined") {
      try {
        viewer.state.restoreState(normalizeNgState(config.ngState));
      } catch (error) {
        console.error("Error restoring viewer state:", error);
      }
      return;
    }

    setTimeout(tryRestoreState, 100);
  }

  function getLink() {
    if (typeof viewer === "undefined") {
      triggerToast("Neuroglancer is still loading");
      return;
    }

    viewer.postJsonState(true, undefined, true, function () {
      const urlPrefix = "https://neuroglancer.neuvue.io/?json_url=";
      copyToClipboard(urlPrefix.concat(viewer.saver.savedUrl));
      triggerToast("Copied link to clipboard");
    });
  }

  function exportTable() {
    const table = document.getElementById("cell-viewer-result-table");
    if (!table) {
      return;
    }

    const rows = Array.from(table.querySelectorAll("tr")).map((row) =>
      Array.from(row.children)
        .map((cell) => `"${cell.textContent.trim().replace(/"/g, '""')}"`)
        .join(",")
    );
    const csv = rows.join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `cell_viewer_${config.viewerType || "results"}_${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function syncViewerModeControls() {
    const selectedMode = document.querySelector('input[name="viewer_type"]:checked');
    const idsLabel = document.getElementById("cellViewerIdsLabel");
    const idsInput = document.getElementById("cellViewerIDsInput");
    const synapseOptions = document.getElementById("synapseOptions");
    const mode = selectedMode ? selectedMode.value : "synapse";
    const isNuclei = mode === "nuclei";
    const isLineage = mode === "lineage";
    const isSynapse = mode === "synapse";

    if (idsLabel) {
      idsLabel.textContent = isNuclei ? "Nucleus ID or Seg ID" : "Root ID";
    }
    if (idsInput) {
      if (isNuclei) {
        idsInput.placeholder = "Enter nucleus or segment IDs separated by commas";
      } else if (isLineage) {
        idsInput.placeholder = "Enter one root ID";
      } else {
        idsInput.placeholder = "Enter root IDs separated by commas";
      }
    }
    if (synapseOptions) {
      synapseOptions.hidden = !isSynapse;
    }
  }

  function initLookupForm() {
    document.querySelectorAll('input[name="viewer_type"]').forEach((input) => {
      input.addEventListener("change", syncViewerModeControls);
    });
    syncViewerModeControls();

    const timestampInput = document.getElementById("timestampInput");

    const lookupForm = document.getElementById("cellViewerLookupForm");
    if (lookupForm) {
      lookupForm.addEventListener("submit", function (event) {
        const formData = new FormData(lookupForm);
        const viewerType = formData.get("viewer_type");

        if (timestampInput && !timestampInput.checkValidity()) {
          event.preventDefault();
          triggerToast(timestampInput.validationMessage || "Timestamp must use YYYY-MM-DD");
          return;
        }

        if (viewerType === "lineage" && String(formData.get("query_ids") || "").includes(",")) {
          event.preventDefault();
          triggerToast("Lineage mode accepts one root ID");
          return;
        }

        triggerLoadingSpinner("submit-spinner");
      });
    }
  }

  function selectID(rootId) {
    if (typeof viewer === "undefined") {
      return;
    }

    const state = viewer.state.toJSON();
    const segLayer = state.layers.find((layer) =>
      ["segmentation", "segmentation_with_graph"].includes(String(layer.type))
    );
    if (!segLayer) {
      return;
    }

    segLayer.segments = segLayer.segments || [];
    segLayer.hiddenSegments = segLayer.hiddenSegments || [];
    const hiddenIndex = segLayer.hiddenSegments.indexOf(rootId);
    if (hiddenIndex > -1) {
      segLayer.segments.push(rootId);
      segLayer.hiddenSegments.splice(hiddenIndex, 1);
      viewer.state.restoreState(state);
    }
  }

  function downloadSVGAsPNG() {
    const svg = document.querySelector("#svg_graph svg");
    if (!svg) {
      return;
    }

    const canvas = document.createElement("canvas");
    const box = svg.viewBox.baseVal;
    const base64doc = btoa(unescape(encodeURIComponent(svg.outerHTML)));
    const width = Math.max(parseInt(box.width, 10), svg.clientWidth || 1) * 10;
    const height = Math.max(parseInt(box.height, 10), svg.clientHeight || 1) * 10;
    const image = document.createElement("img");
    image.src = "data:image/svg+xml;base64," + base64doc;
    image.onload = function () {
      canvas.setAttribute("width", width);
      canvas.setAttribute("height", height);
      canvas.getContext("2d").drawImage(image, 0, 0, width, height);
      const link = document.createElement("a");
      link.download = `lineage_graph_${Date.now()}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    };
  }

  function initLineageGraph() {
    const graph = document.getElementById("svg_graph");
    if (!graph) {
      return;
    }

    graph.querySelectorAll("svg").forEach((svg) => {
      svg.setAttribute("width", "100%");
      svg.setAttribute("height", "100%");
    });

    graph.querySelectorAll(".node").forEach((node) => {
      const rootId = node.textContent.trim().split(/\s+/)[0];
      node.style.cursor = "pointer";
      node.addEventListener("click", function () {
        selectID(rootId);
      });
    });

    const downloadButton = document.getElementById("downloadLineagePNG");
    if (downloadButton) {
      downloadButton.addEventListener("click", downloadSVGAsPNG);
    }
  }

  function initActions() {
    const copyNgLinkButton = document.getElementById("btnCopyNgLink");
    if (copyNgLinkButton) {
      copyNgLinkButton.addEventListener("click", getLink);
    }

    const copyInfoButton = document.getElementById("btnCopyCellInfo");
    if (copyInfoButton) {
      copyInfoButton.addEventListener("click", function () {
        copyToClipboard(copyInfoButton.dataset.copyValue || "");
        triggerToast("Copied table info");
      });
    }

    const exportInfoButton = document.getElementById("btnExportCellInfo");
    if (exportInfoButton) {
      exportInfoButton.addEventListener("click", exportTable);
    }

    document.querySelectorAll("[data-exit-url]").forEach((button) => {
      button.addEventListener("click", function () {
        document.location =
          button.dataset.exitUrl ||
          (config.urls && config.urls.cellViewer) ||
          "/cell-viewer/";
      });
    });
  }

  window.openSideMenu = openSideMenu;
  window.closeSideMenu = closeSideMenu;
  window.sidemenu_content = sidemenuContent;
  window.getLink = getLink;
  window.triggerToast = triggerToast;
  window.selectID = selectID;
  window.downloadSVGAsPNG = downloadSVGAsPNG;

  document.addEventListener("DOMContentLoaded", function () {
    initLookupForm();
    initActions();
    initLineageGraph();

    if (config.ngState) {
      if (window.localStorage.getItem("sidebarStatus") === "closed") {
        closeSideMenu();
      } else {
        openSideMenu();
      }
      tryRestoreState();
    }
  });

  window.addEventListener("pageshow", function () {
    if (document.getElementById("submit-spinner") !== null) {
      removeLoadingSpinner("submit-spinner", "Open Cell Viewer");
    }
  });
})();
