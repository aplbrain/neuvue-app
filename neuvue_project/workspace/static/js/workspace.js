(function () {
  const configElement = document.getElementById("workspace-config");
  const config = configElement ? JSON.parse(configElement.textContent) : {};
  const trackedNewOperations = new Set();
  let currentButtonSelection = "noneSelected";
  let browserTimer = null;
  const hideHotkeysStorageKey = "neuvue:workspace-hide-hotkeys";

  function uniqueTags(tags) {
    return Array.from(
      new Set((tags || []).map((tag) => String(tag).trim()).filter(Boolean))
    );
  }

  function initTags() {
    const input = document.querySelector('input[name="tags"]');
    if (!input || !window.Tagify) {
      return;
    }

    const whitelist = uniqueTags((config.namespaceTags || []).concat(config.recentTags || []));
    new Tagify(input, {
      whitelist: whitelist,
      enforceWhitelist: false,
      originalInputValueFormat: (valuesArr) => valuesArr.map((item) => item.value).join(","),
      maxTags: 10,
      dropdown: {
        maxItems: 20,
        classname: "tags-look",
        enabled: 0,
        closeOnSelect: true,
        fuzzySearch: true,
      },
    });
  }

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
      neuroglancerWindow.style.width = open ? "calc(100% - 330px)" : "calc(100% - 42px)";
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

  function getLink() {
    if (config.ngHost === "neuvue") {
      viewer.postJsonState(true, undefined, true, function () {
        const urlPrefix = "https://neuroglancer.neuvue.io/?json_url=";
        copyToClipboard(urlPrefix.concat(viewer.saver.savedUrl));
        triggerToast("Copied link to clipboard");
      });
      return;
    }

    if (config.ngHost === "spelunker") {
      const urlPrefix = "https://spelunker.cave-explorer.org/#!";
      copyToClipboard(urlPrefix.concat(JSON.stringify(viewer.state.toJSON())));
      triggerToast("Copied link to clipboard");
      return;
    }

    triggerToast("Copy Link unavailable on embedded Neuroglancer task type");
  }

  function saveState() {
    if (config.ngHost !== "neuvue") {
      triggerToast("State saving disabled for non-native Neuroglancer");
      removeLoadingSpinner("save_state", "Save State");
      return;
    }

    viewer.postJsonState(true, undefined, true, function () {
      const postBody = JSON.stringify({
        task_id: config.taskId,
        ng_state: viewer.saver.savedUrl,
      });
      fetch(config.urls.saveState, {
        body: postBody,
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        method: "POST",
      }).then((response) => {
        response.text().then((text) => {
          removeLoadingSpinner("save_state", "Save State");
          triggerToast(text);
        });
      });
    });
  }

  function applyNgStatePlugin() {
    const previousState = viewer.state.toJSON();
    const pluginInputs = getNgStatePluginInputs();
    if (pluginInputs === null) {
      return;
    }

    const postBody = JSON.stringify({
      namespace: config.namespace,
      ng_state: previousState,
      plugin_inputs: pluginInputs,
    });

    fetch(config.urls.ngStatePlugin, {
      body: postBody,
      headers: { "X-CSRFToken": getCookie("csrftoken") },
      method: "POST",
    }).then((response) => {
      return response.text().then((text) => {
        let jsonResponse = {};
        try {
          jsonResponse = text ? JSON.parse(text) : {};
        } catch (error) {
          jsonResponse = {
            message: text || "Plugin returned an unreadable response.",
          };
        }

        if (!response.ok) {
          const message = jsonResponse.message || `Plugin failed with status ${response.status}.`;
          console.error(message, jsonResponse.additional_info || {});
          triggerToast(message);
          return;
        }

        const ngState = jsonResponse.ngstate;
        if (ngState) {
          try {
            viewer.state.restoreState(ngState);
          } catch (error) {
            console.error(
              "Plugin returned an unrestorable Neuroglancer state:",
              error,
              jsonResponse.additional_info || {}
            );
            try {
              viewer.state.restoreState(previousState);
            } catch (rollbackError) {
              console.error("Could not restore the previous Neuroglancer state:", rollbackError);
            }
            triggerToast(`Plugin returned an unrestorable Neuroglancer state: ${error.message || error}`);
            return;
          }
        }

        triggerToast(jsonResponse.message || "Plugin executed successfully.");
      });
    }).catch((error) => {
      const message = `Plugin request failed before reaching the server: ${error.message || error}`;
      console.error(message);
      triggerToast(message);
    });
  }

  function getNgStatePluginInputs() {
    const pluginInputs = {};
    let missingRequiredInput = null;

    document.querySelectorAll(".ngStatePluginInput").forEach((input) => {
      const name = input.dataset.pluginInputName;
      if (!name) {
        return;
      }

      if (input.type === "checkbox") {
        pluginInputs[name] = input.checked;
        if (input.required && !input.checked && missingRequiredInput === null) {
          missingRequiredInput = input;
        }
        return;
      }

      const value = typeof input.value === "string" ? input.value.trim() : input.value;
      pluginInputs[name] = value;
      if (input.required && !value && missingRequiredInput === null) {
        missingRequiredInput = input;
      }
    });

    if (missingRequiredInput !== null) {
      const details = missingRequiredInput.closest("details");
      if (details) {
        details.open = true;
        const panel = details.closest("[data-autocollapse-panel]");
        if (panel) {
          panel.classList.remove("nv-plugin-panel-collapsed");
        }
      }
      missingRequiredInput.focus();
      const label = missingRequiredInput.closest(".nv-plugin-field");
      const labelText = label ? label.querySelector(".nv-plugin-label") : null;
      triggerToast(`${labelText ? labelText.textContent.trim() : "Plugin input"} is required.`);
      return null;
    }

    return pluginInputs;
  }

  function initPluginPanels() {
    const sidecontent = document.getElementById("neuVue-sidecontent");
    if (!sidecontent) {
      return;
    }

    document.querySelectorAll("[data-autocollapse-panel] details").forEach((details) => {
      details.open = true;
      const panel = details.closest("[data-autocollapse-panel]");
      if (!panel) {
        return;
      }

      const maxOpenHeight = Math.max(220, sidecontent.clientHeight * 0.42);
      if (panel.scrollHeight > maxOpenHeight) {
        details.open = false;
        panel.classList.add("nv-plugin-panel-collapsed");
      }

      details.addEventListener("toggle", function () {
        panel.classList.toggle("nv-plugin-panel-collapsed", !details.open);
      });
    });
  }

  function show3DSlices() {
    if (config.showSlices === true && !viewer.showPerspectiveSliceViews.value_) {
      viewer.showPerspectiveSliceViews.toggle();
    }
  }

  function getSelectedSegments() {
    const selectedSegments = new Set();
    viewer.state.toJSON().layers.forEach((layer) => {
      if (layer.type === "segmentation_with_graph" || layer.type === "segmentation") {
        layer.segments.forEach((segment) => {
          selectedSegments.add(segment);
        });
      }
    });
    return Array.from(selectedSegments);
  }

  function saveOperations() {
    const postBody = JSON.stringify({
      task_id: config.taskId,
      operation_ids: Array.from(trackedNewOperations),
      namespace: config.namespace,
    });
    fetch(config.urls.saveOperations, {
      body: postBody,
      headers: { "X-CSRFToken": getCookie("csrftoken") },
      method: "POST",
    }).then((response) => {
      response.text().then((text) => {
        triggerToast(text);
      });
    });
  }

  function updateTrackedOperations(currentOperationIds) {
    if (!currentOperationIds || !currentOperationIds.length) {
      return;
    }

    currentOperationIds.forEach((operationId) => {
      if (!trackedNewOperations.has(operationId)) {
        trackedNewOperations.add(operationId);
        saveOperations();
        const numEditsDiv = document.getElementById("num_edits");
        if (numEditsDiv) {
          numEditsDiv.innerHTML = Number(config.numEdits || 0) + trackedNewOperations.size;
        }
      }
    });
  }

  function getOperationIdsFromSpelunker() {
    for (let i = 0; i < viewer.layerManager.managedLayers.length; i += 1) {
      const layer = viewer.layerManager.managedLayers[i].layer_;
      if (layer.type === "segmentation") {
        const operationIds = layer.graphConnection.value.operationIds.toString();
        return operationIds.split(",").map(Number);
      }
    }
    return [];
  }

  function appendHiddenInput(form, name, value) {
    $("<input>").attr("type", "hidden").attr("name", name).attr("value", value).appendTo(form);
  }

  function submitForm(value, formSelector = "#mainForm") {
    window.removeEventListener("beforeunload", exitAlert);
    const duration = Math.round(browserTimer.getTimeInMilliseconds() / 1000);

    appendHiddenInput(formSelector, "button", value);
    appendHiddenInput(formSelector, "duration", duration);
    appendHiddenInput(formSelector, "taskId", config.taskId);

    if (config.ngUrl) {
      $(formSelector).submit();
      return;
    }

    if (config.ngHost === "spelunker") {
      appendHiddenInput(formSelector, "ngState", JSON.stringify(viewer.state.toJSON()));
      if (config.trackSelectedSegments) {
        appendHiddenInput(formSelector, "selected_segments", getSelectedSegments());
      }
      $(formSelector).submit();
      return;
    }

    viewer.postJsonState(true, undefined, true, function () {
      let state = viewer.saver.savedUrl;
      if (!state) {
        state = JSON.stringify(viewer.state.toJSON());
      }

      appendHiddenInput(formSelector, "ngState", state);
      appendHiddenInput(formSelector, "ngDifferStack", JSON.stringify(viewer.differ.stack));
      if (config.trackSelectedSegments) {
        appendHiddenInput(formSelector, "selected_segments", getSelectedSegments());
      }
      $(formSelector).submit();
    });
  }

  function exitAlert(event) {
    event.preventDefault();
    event.returnValue = "";
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

  function updateButtonSelected(buttonTitle) {
    if (currentButtonSelection !== "noneSelected") {
      const previouslySelectedButton = document.getElementById(currentButtonSelection);
      if (previouslySelectedButton) {
        previouslySelectedButton.classList.toggle("active");
      }
    }

    currentButtonSelection = buttonTitle;
    const selectedButton = document.getElementById(buttonTitle);
    if (selectedButton) {
      selectedButton.classList.toggle("active");
    }
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

  function submitWithSelectedSegmentsCheck(buttonId, buttonSubmissionValue, buttonDisplayName) {
    if (config.numberOfSelectedSegmentsExpected) {
      const numSelectedSegments = getSelectedSegments().length;
      if (numSelectedSegments > Number(config.numberOfSelectedSegmentsExpected)) {
        showConfirmSelectedSegmentsModal(
          buttonId,
          buttonSubmissionValue,
          buttonDisplayName,
          numSelectedSegments
        );
        return;
      }
    }

    submitForm(buttonSubmissionValue);
  }

  function initHotkeyHints() {
    const os = navigator.platform.toLowerCase();
    const modifier = os.includes("mac") ? "⌥" : "Alt";

    document.querySelectorAll(".hotkeyHint").forEach((hotkeyHint) => {
      const modifierText = hotkeyHint.querySelector(".modifier");
      if (modifierText) {
        modifierText.innerHTML = modifier;
      }
    });

    document.querySelectorAll(".forcedChoiceHotkeyHint").forEach((hotkeyHint) => {
      const hotkeyText = hotkeyHint.querySelector(".hotkey_button");
      if (hotkeyText && !hotkeyText.innerHTML.toLowerCase().includes("none")) {
        hotkeyHint.style.display = "block";
      }
    });
  }

  function setHotkeysHidden(hidden) {
    document.body.classList.toggle("nv-hide-hotkeys", hidden);
    window.localStorage.setItem(hideHotkeysStorageKey, hidden ? "true" : "false");
  }

  function initHotkeyToggle() {
    const toggle = document.getElementById("hideHotkeysToggle");
    const shouldHideHotkeys = window.localStorage.getItem(hideHotkeysStorageKey) === "true";

    setHotkeysHidden(shouldHideHotkeys);

    if (!toggle) {
      return;
    }

    toggle.checked = shouldHideHotkeys;
    toggle.addEventListener("change", function () {
      setHotkeysHidden(toggle.checked);
    });
  }

  function initButtons() {
    if (config.submitTaskButton) {
      if (config.buttonList && config.buttonList.length) {
        $("#btnSubmit").click(function () {
          if (currentButtonSelection !== "noneSelected") {
            triggerLoadingSpinner("submit_task_load");
            submitWithSelectedSegmentsCheck("submit_task_load", currentButtonSelection, "Submit Task");
          } else {
            alert("Please select a decision!");
          }
        });
      } else {
        $("#btnSubmit").click(function () {
          triggerLoadingSpinner("submit_task_load");
          submitWithSelectedSegmentsCheck("submit_task_load", "submit", "Submit Task");
        });
      }
    } else {
      (config.buttonList || []).forEach((button) => {
        $("#" + button.submission_value).click(function () {
          submitWithSelectedSegmentsCheck(
            button.submission_value + "_load",
            button.submission_value,
            button.display_name
          );
        });
      });
    }

    $("#btnSkipSubmit").click(function () {
      submitForm("skip");
    });

    $("#btnRemoveSubmit").click(function () {
      submitForm("remove");
    });

    $("#btnFlagSubmit").click(function () {
      submitForm("flag", "#flagForm");
    });

    $("#btnSaveState").click(function () {
      saveState();
    });

    $("#btnStop").click(function () {
      submitForm("stop");
    });

    $("#btnStart").click(function () {
      appendHiddenInput("#mainForm", "button", "start");
      $("#mainForm").submit();
    });

    $("#timeoutModalNo").click(function () {
      submitForm("stop");
    });
  }

  function initKeyboard() {
    const buttonIdToHotkey = {};
    (config.buttonList || []).forEach((button) => {
      buttonIdToHotkey[button.submission_value] = button.hotkey;
    });

    document.addEventListener("keydown", function (event) {
      const charToKeyCode = {
        c: 67,
        d: 68,
        j: 74,
        m: 77,
        q: 81,
        r: 82,
        t: 84,
        v: 86,
        w: 87,
        y: 89,
        z: 90,
      };

      document.querySelectorAll(".forcedChoiceButton").forEach((button) => {
        const buttonHotkey = buttonIdToHotkey[button.id];
        if (event.altKey && event.keyCode === charToKeyCode[buttonHotkey]) {
          button.click();
        }
      });

      if (event.altKey && event.keyCode === 75) {
        $("#btnSkipSubmit").click();
      } else if (event.altKey && event.keyCode === 70) {
        $("#btnFlag").click();
      } else if (event.altKey && event.keyCode === 69) {
        $("#btnStop").click();
      }
    });

    document.addEventListener(
      "wheel",
      (event) => {
        if (event.ctrlKey) {
          event.preventDefault();
        }
      },
      { passive: false }
    );
  }

  function initTimer() {
    browserTimer = new browserInteractionTime({
      timeIntervalEllapsedCallbacks: [
        {
          timeInMilliseconds: 60000,
          callback: () => saveState(),
          multiplier: (x) => x + 3e5,
        },
      ],
      absoluteTimeEllapsedCallbacks: [],
      browserTabInactiveCallbacks: [],
      browserTabActiveCallbacks: [],
      idleTimeoutMs: 10000,
      checkCallbacksIntervalMs: 250,
    });
    browserTimer.startTimer();
  }

  function initViewer() {
    if (!config.ngUrl) {
      tryRestoreState();
      window.setInterval(function () {
        console.log("skipping operation_ids");
      }, 3000);
    }
    show3DSlices();
  }

  window.openSideMenu = openSideMenu;
  window.closeSideMenu = closeSideMenu;
  window.sidemenu_content = sidemenuContent;
  window.getLink = getLink;
  window.saveState = saveState;
  window.applyNgStatePlugin = applyNgStatePlugin;
  window.getNgStatePluginInputs = getNgStatePluginInputs;
  window.getSelectedSegments = getSelectedSegments;
  window.submitForm = submitForm;
  window.triggerToast = triggerToast;
  window.updateButtonSelected = updateButtonSelected;
  window.updateTrackedOperations = updateTrackedOperations;
  window.getOperationIdsFromSpelunker = getOperationIdsFromSpelunker;

  $(document).ready(function () {
    initTags();
    initTimer();
    if (window.localStorage.getItem("sidebarStatus") === "closed") {
      closeSideMenu();
    } else {
      openSideMenu();
    }
    initViewer();
    initHotkeyHints();
    initHotkeyToggle();
    initPluginPanels();
    initButtons();
    initKeyboard();

    if (config.taskId) {
      window.addEventListener("beforeunload", exitAlert);
    }
  });
})();
