#!/usr/bin/env python3
"""
Semi-automated script to update screenshots for `getting_started.md`

Usage:
    Must pre-authorize middleware for datastack.

    Close all chrome windows associated with the gmail for middle auth.

    Run the following:
        open -na "Google Chrome" --args \
            --remote-debugging-port=9222 \
            --user-data-dir="$PWD/.screenshot-chrome-profile"

    Log-in to your neuvue account, go to a task from
    DOCUMENTATION_NAMESPACE and ensure middle-auth is configured.

    Run:
        python screenshot_updater.py

    The script will pause two times: once at the task page, and once at
    inspect task. These are additional opportunities to dismiss any pop-ups
    before the screenshot is logged.

    After the script has completed: python manage.py collectstatic will
    complete the documentation update.

Environment variables:
    NEUVUE_URL - Base URL (default: http://localhost:8000)
    DOCUMENTATION_NAMESPACE - Namespace to capture
    DOCUMENTATION_TASK_ID - Task ID to inspect
"""

import asyncio
import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
BASE_URL = os.environ.get("NEUVUE_URL", "http://localhost:8000")
DOCUMENTATION_USERNAME = os.environ.get("DOCUMENTATION_USERNAME")
DOCUMENTATION_PASSWORD = os.environ.get("DOCUMENTATION_PASSWORD")
# Define variables for task/synapse IDs and namespace
DOCUMENTATION_NAMESPACE = os.environ.get(
    "DOCUMENTATION_NAMESPACE", "v1dd_split_validation_hc"
)
DOCUMENTATION_TASK_ID = os.environ.get("TASK_ID", "69ed038caf31f6146ab16a15")
# SYNAPSE_ID = os.environ.get("SYNAPSE_ID", "1")

# Paths
PROJECT_ROOT = Path(__file__).parent
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
STATIC_DIR = PROJECT_ROOT / "neuvue_project" / "workspace" / "static"
STATIC_SCREENSHOTS_DIR = STATIC_DIR / "screenshots"
GETTING_STARTED_PATH = STATIC_DIR / "getting_started.md"
CHROME_PROFILE_DIR = PROJECT_ROOT / ".screenshot-chrome-profile"

SCREENSHOTS_DIR.mkdir(exist_ok=True)
STATIC_SCREENSHOTS_DIR.mkdir(exist_ok=True)


# Mapping of screenshots to markdown sections. Matching is done on the `alt`
# attribute rather than the `src`, so this keeps working after the first run
# replaces the imgur links with local screenshot paths.
SCREENSHOT_MAPPING = {
    "01_main_landing_page": "Home Page",
    "02_tasks_page": "Task Page",
    "03_pending_tasks_panel": "Pending Table",
    "04_closed_tasks_panel": "Closed Table",
    "05_workspace_page": "Workspace Page",
    "06_inspect_task": "Inspect Task Page",
    # "07_inspect_synapse": "Synapse Viewer Page",
    "08_neuroglancer_preferences": "User Preferences",
}


def copy_screenshots_to_static():
    """Copy numbered screenshots to static, overwriting existing files."""
    print("\n--- Copying Screenshots to Static Directory ---")

    STATIC_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    for screenshot_name in SCREENSHOT_MAPPING:
        src = SCREENSHOTS_DIR / f"{screenshot_name}.png"
        dst = STATIC_SCREENSHOTS_DIR / f"{screenshot_name}.png"

        if src.exists():
            shutil.copy2(src, dst)
            print(f"  ✓ Overwrote {dst.name}")
        else:
            print(f"  ✗ Could not find {src.name}")


def update_markdown():
    """Update getting_started.md with new screenshot references."""
    print("\n--- Updating Getting Started Markdown ---")

    if not GETTING_STARTED_PATH.exists():
        print(f"  ✗ File not found: {GETTING_STARTED_PATH}")
        return False

    # Read the markdown file
    with open(GETTING_STARTED_PATH, "r") as f:
        content = f.read()

    original_content = content

    # Replace each screenshot, matching on the `alt` attribute so this works
    # whether `src` currently points at an imgur link or a prior local path.
    for screenshot_name, alt in SCREENSHOT_MAPPING.items():
        pattern = rf'<img src="[^"]*" alt="{re.escape(alt)}"[^>]*>'
        new_img = (
            f'<img src="screenshots/{screenshot_name}.png" alt="{alt}" width="800"/>'
        )

        if re.search(pattern, content):
            content = re.sub(pattern, new_img, content)
            print(f"  ✓ Updated {alt}")
        else:
            print(f"  ⚠ Pattern not found for {alt}")

    # Write back if changes were made
    if content != original_content:
        with open(GETTING_STARTED_PATH, "w") as f:
            f.write(content)
        print(f"\n  ✓ Updated {GETTING_STARTED_PATH}")
        return True
    else:
        print("\n  ⚠ No changes made to markdown")
        return False


async def login(page):
    """Log in to NeuVue unless the persistent profile is already authenticated."""
    await page.goto(
        f"{BASE_URL.rstrip('/')}/accounts/login/",
        wait_until="domcontentloaded",
    )

    print("Login URL:", page.url)
    print("Login title:", await page.title())

    # An authenticated session may redirect away from the login page.
    if "/accounts/login" not in page.url:
        print("Existing NeuVue session found.")
        return

    username_input = page.locator("#id_login")
    password_input = page.locator("#id_password")

    if await username_input.count() == 0:
        print("Login form not present; continuing with existing session.")
        return

    await username_input.wait_for(
        state="visible",
        timeout=30_000,
    )

    await username_input.fill(DOCUMENTATION_USERNAME)
    await password_input.fill(DOCUMENTATION_PASSWORD)

    async with page.expect_navigation(
        wait_until="domcontentloaded",
    ):
        await page.get_by_role(
            "button",
            name="Sign In",
        ).click()

    print("After login URL:", page.url)

    if "/accounts/login" in page.url:
        raise RuntimeError("NeuVue login did not complete successfully.")


async def collapse_django_debug_toolbar(page):
    """Collapse the Django Debug Toolbar when it is present and expanded."""
    debug_toolbar = page.locator("#djDebug")
    hide_button = page.locator("#djHideToolBarButton")

    if await debug_toolbar.count() == 0:
        return

    try:
        await debug_toolbar.wait_for(
            state="attached",
            timeout=2_000,
        )

        if await hide_button.count() > 0 and await hide_button.is_visible():
            await hide_button.click()

            await page.wait_for_function(
                """() => {
                    const toolbar = document.getElementById("djDebugToolbar");
                    const handle = document.getElementById("djDebugToolbarHandle");

                    return (
                        !toolbar ||
                        window.getComputedStyle(toolbar).display === "none" ||
                        (handle && window.getComputedStyle(handle).display !== "none")
                    );
                }""",
                timeout=2_000,
            )
    except Exception as exc:
        print(f"  Note: Could not collapse Django Debug Toolbar: {exc}")


async def take_screenshot(
    page,
    name,
    description="",
    *,
    full_page=False,
):
    """Capture a screenshot after collapsing the Django Debug Toolbar."""
    filename = SCREENSHOTS_DIR / f"{name}.png"

    await collapse_django_debug_toolbar(page)

    await page.screenshot(
        path=str(filename),
        full_page=full_page,
    )

    print(f"  ✓ {description or name} → {filename}")
    return filename


async def wait_for_manual_auth(page, page_name):
    """Pause while the user completes MiddleAuth."""
    print("\n" + "=" * 68)
    print(f"MIDDLEAUTH CHECK: {page_name}")
    print("=" * 68)
    print("In Chrome:")
    print("  1. Click 'Request login' in the gray MiddleAuth banner.")
    print("  2. Complete the authorization flow.")
    print("  3. Wait until the gray banner disappears.")

    while True:
        answer = await asyncio.to_thread(
            input,
            "Has the MiddleAuth banner disappeared? [y/n]: ",
        )

        if answer.strip().lower() in {"y", "yes"}:
            break

        print("Complete MiddleAuth in Chrome, then try again.")

    try:
        await page.wait_for_load_state(
            "domcontentloaded",
            timeout=15_000,
        )
    except Exception:
        pass

    await page.wait_for_timeout(2_000)
    print("Continuing at:", page.url)


async def screenshot_main_landing_page(page):
    """Capture main landing page while logged in."""
    print("\n--- Main Landing Page (Logged In) ---")
    await page.goto(f"{BASE_URL}/")
    await page.wait_for_load_state("networkidle")
    await take_screenshot(
        page,
        "01_main_landing_page",
        "Main landing page",
        full_page=True,
    )


async def screenshot_tasks_page(page):
    """Capture the Tasks page."""
    print("\n--- Tasks Page ---")

    response = await page.goto(
        f"{BASE_URL}/tasks/",
        wait_until="domcontentloaded",
    )

    status = response.status if response else None
    print("Status:", status)
    print("Current URL:", page.url)
    print("Title:", await page.title())

    if response is None or not response.ok:
        raise RuntimeError(f"Tasks request failed with HTTP {status}: {page.url}")

    # Catch authentication redirects before waiting on page-specific content.
    if "/accounts/login" in page.url:
        raise RuntimeError(
            "The Tasks page redirected to login. "
            "The session may not be authenticated."
        )

    tasks_page = page.locator(".nv-page")
    queue_list = page.locator(".nv-queue-list")

    try:
        await tasks_page.wait_for(
            state="visible",
            timeout=15_000,
        )
        await queue_list.wait_for(
            state="visible",
            timeout=15_000,
        )
    except Exception:
        print("Page body:", (await page.locator("body").inner_text())[:2_000])
        await page.screenshot(
            path=str(SCREENSHOTS_DIR / "tasks_page_error.png"),
            full_page=True,
        )
        raise

    await take_screenshot(
        page,
        "02_tasks_page",
        "Tasks page",
        full_page=False,
    )


async def screenshot_pending_tasks_panel(page, namespace=DOCUMENTATION_NAMESPACE):
    """Capture the pending-tasks panel for a namespace."""
    print(f"\n--- Pending Tasks Panel ({namespace}) ---")

    response = await page.goto(
        f"{BASE_URL}/tasks/",
        wait_until="domcontentloaded",
    )

    status = response.status if response else None
    print("Status:", status)
    print("Current URL:", page.url)

    if response is None or not response.ok:
        raise RuntimeError(f"Tasks request failed with HTTP {status}: {page.url}")

    if "/accounts/login" in page.url:
        raise RuntimeError(
            "The Tasks page redirected to login. "
            "The session may not be authenticated."
        )

    await page.locator(".nv-queue-list").wait_for(
        state="visible",
        timeout=15_000,
    )

    # The namespace appears in the proofreading workspace URL.
    workspace_link = page.locator(f'a.js-loading-link[href$="/{namespace}"]').first

    if await workspace_link.count() == 0:
        raise RuntimeError(
            f"Namespace {namespace!r} was not found on the Tasks page. "
            "No proofreading workspace link matched that namespace."
        )

    task_card = workspace_link.locator("xpath=ancestor::article[@data-task-card]")

    await task_card.wait_for(
        state="visible",
        timeout=10_000,
    )

    panel_toggle = task_card.locator(".js-task-panel-toggle")
    task_panel = task_card.locator(".nv-task-panel")
    pending_tab = task_card.locator('.js-task-tab[data-target^="pending-panel-"]')
    pending_panel = task_card.locator('.nv-tab-panel[id^="pending-panel-"]')

    await panel_toggle.wait_for(
        state="visible",
        timeout=5_000,
    )

    if await panel_toggle.get_attribute("aria-expanded") != "true":
        await panel_toggle.click()

    await task_panel.wait_for(
        state="visible",
        timeout=5_000,
    )

    if await pending_tab.get_attribute("aria-selected") != "true":
        await pending_tab.click()

    await pending_panel.wait_for(
        state="visible",
        timeout=5_000,
    )

    await task_card.scroll_into_view_if_needed()

    await take_screenshot(
        page,
        "03_pending_tasks_panel",
        f"Pending tasks ({namespace})",
        full_page=False,
    )


async def screenshot_closed_tasks_panel(page, namespace=DOCUMENTATION_NAMESPACE):
    """Capture the closed-tasks panel for a namespace."""
    print(f"\n--- Closed Tasks Panel ({namespace}) ---")

    response = await page.goto(
        f"{BASE_URL}/tasks/",
        wait_until="domcontentloaded",
    )

    status = response.status if response else None
    print("Status:", status)
    print("Current URL:", page.url)

    if response is None or not response.ok:
        raise RuntimeError(f"Tasks request failed with HTTP {status}: {page.url}")

    if "/accounts/login" in page.url:
        raise RuntimeError(
            "The Tasks page redirected to login. "
            "The session may not be authenticated."
        )

    await page.locator(".nv-queue-list").wait_for(
        state="visible",
        timeout=15_000,
    )

    # Locate the namespace card using its workspace link. This supports both
    # regular workspace and spelunker-workspace URLs.
    workspace_link = page.locator(f'a.js-loading-link[href$="/{namespace}"]').first

    if await workspace_link.count() == 0:
        raise RuntimeError(
            f"Namespace {namespace!r} was not found on the Tasks page. "
            "No proofreading workspace link matched that namespace."
        )

    task_card = workspace_link.locator("xpath=ancestor::article[@data-task-card]")

    await task_card.wait_for(
        state="visible",
        timeout=10_000,
    )

    panel_toggle = task_card.locator(".js-task-panel-toggle")
    task_panel = task_card.locator(".nv-task-panel")
    closed_tab = task_card.locator('.js-task-tab[data-target^="closed-panel-"]')
    closed_panel = task_card.locator('.nv-tab-panel[id^="closed-panel-"]')

    await panel_toggle.wait_for(
        state="visible",
        timeout=5_000,
    )

    # Expand the namespace card when necessary.
    if await panel_toggle.get_attribute("aria-expanded") != "true":
        await panel_toggle.click()

    await task_panel.wait_for(
        state="visible",
        timeout=5_000,
    )

    await closed_tab.wait_for(
        state="visible",
        timeout=5_000,
    )

    # Select the Closed tab when necessary.
    if await closed_tab.get_attribute("aria-selected") != "true":
        await closed_tab.click()

    await closed_panel.wait_for(
        state="visible",
        timeout=5_000,
    )

    tab_id = await closed_tab.get_attribute("id")
    panel_id = await closed_panel.get_attribute("id")

    if not tab_id or not panel_id:
        raise RuntimeError(
            f"Could not determine the Closed tab or panel IDs for "
            f"namespace {namespace!r}."
        )

    # Verify that the click updated both the tab and panel states.
    await page.wait_for_function(
        """({ tabId, panelId }) => {
            const tab = document.getElementById(tabId);
            const panel = document.getElementById(panelId);

            return Boolean(
                tab &&
                panel &&
                tab.getAttribute("aria-selected") === "true" &&
                tab.classList.contains("active") &&
                !panel.hidden &&
                window.getComputedStyle(panel).display !== "none"
            );
        }""",
        arg={
            "tabId": tab_id,
            "panelId": panel_id,
        },
        timeout=5_000,
    )

    await task_card.scroll_into_view_if_needed()

    await take_screenshot(
        page,
        "04_closed_tasks_panel",
        f"Closed tasks ({namespace})",
        full_page=False,
    )


async def screenshot_workspace_page(page, namespace=DOCUMENTATION_NAMESPACE):
    """Capture the correct workspace page for a namespace."""
    print(f"\n--- Workspace Page ({namespace}) ---")

    tasks_response = await page.goto(
        f"{BASE_URL.rstrip('/')}/tasks/",
        wait_until="domcontentloaded",
    )

    tasks_status = tasks_response.status if tasks_response else None

    if tasks_response is None or not tasks_response.ok:
        raise RuntimeError(f"Tasks request failed with HTTP {tasks_status}: {page.url}")

    if "/accounts/login" in page.url:
        raise RuntimeError("The Tasks page redirected to login.")

    await page.locator(".nv-queue-list").wait_for(
        state="visible",
        timeout=15_000,
    )

    workspace_link = page.locator(f'a.js-loading-link[href$="/{namespace}"]').first

    if await workspace_link.count() == 0:
        raise RuntimeError(f"No workspace link was found for namespace {namespace!r}.")

    workspace_href = await workspace_link.get_attribute("href")

    if not workspace_href:
        raise RuntimeError(
            f"The workspace link for namespace {namespace!r} "
            "does not contain an href."
        )

    print("Workspace href:", workspace_href)

    if workspace_href.startswith(("http://", "https://")):
        workspace_url = workspace_href
    else:
        workspace_url = f"{BASE_URL.rstrip('/')}/" f"{workspace_href.lstrip('/')}"

    response = await page.goto(
        workspace_url,
        wait_until="domcontentloaded",
    )

    initial_status = response.status if response else None
    print("Initial status:", initial_status)
    print("Initial URL:", page.url)

    if response is None or not response.ok:
        body_text = await page.locator("body").inner_text()

        raise RuntimeError(
            f"Workspace request failed with HTTP {initial_status}: "
            f"{page.url}\n"
            f"Response body:\n{body_text[:2_000]}"
        )

    workspace_page = page.locator(".nv-workspace-page")
    workspace_main = page.locator(".nv-workspace-main")

    await workspace_page.wait_for(
        state="visible",
        timeout=30_000,
    )

    await workspace_main.wait_for(
        state="visible",
        timeout=30_000,
    )

    await wait_for_manual_auth(
        page,
        f"Workspace Page ({namespace})",
    )

    await take_screenshot(
        page,
        "05_workspace_page",
        f"Workspace page ({namespace})",
        full_page=False,
    )


async def screenshot_inspect_task(
    page,
    task_id=DOCUMENTATION_TASK_ID,
    namespace=DOCUMENTATION_NAMESPACE,
):
    """Capture the inspect page using the namespace's workspace type."""
    print(f"\n--- Inspect Task Page (ID: {task_id}) ---")

    tasks_response = await page.goto(
        f"{BASE_URL.rstrip('/')}/tasks/",
        wait_until="domcontentloaded",
    )

    tasks_status = tasks_response.status if tasks_response else None

    if tasks_response is None or not tasks_response.ok:
        raise RuntimeError(f"Tasks request failed with HTTP {tasks_status}: {page.url}")

    if "/accounts/login" in page.url:
        raise RuntimeError("The Tasks page redirected to login.")

    await page.locator(".nv-queue-list").wait_for(
        state="visible",
        timeout=15_000,
    )

    workspace_link = page.locator(f'a.js-loading-link[href$="/{namespace}"]').first

    if await workspace_link.count() == 0:
        raise RuntimeError(f"No workspace link was found for namespace {namespace!r}.")

    workspace_href = await workspace_link.get_attribute("href")

    if not workspace_href:
        raise RuntimeError(
            f"The workspace link for namespace {namespace!r} "
            "does not contain an href."
        )

    if workspace_href.startswith("/spelunker-workspace/"):
        inspect_path = f"/spelunker-workspace/inspect/{task_id}"
    elif workspace_href.startswith("/workspace/"):
        inspect_path = f"/workspace/inspect/{task_id}"
    else:
        inspect_path = f"/inspect/{task_id}"

    inspect_url = f"{BASE_URL.rstrip('/')}{inspect_path}"

    print("Inspect URL:", inspect_url)

    response = await page.goto(
        inspect_url,
        wait_until="domcontentloaded",
    )

    initial_status = response.status if response else None
    print("Initial status:", initial_status)
    print("Initial URL:", page.url)

    if response is None or not response.ok:
        body_text = await page.locator("body").inner_text()

        raise RuntimeError(
            f"Inspect task request failed with HTTP {initial_status}: "
            f"{page.url}\n"
            f"Response body:\n{body_text[:4_000]}"
        )

    inspect_page = page.locator(
        ".nv-workspace-page, " ".inspect-task-container, " "#neuroglancer"
    ).first

    await inspect_page.wait_for(
        state="visible",
        timeout=30_000,
    )

    await wait_for_manual_auth(
        page,
        f"Inspect Task Page ({task_id})",
    )

    await take_screenshot(
        page,
        "06_inspect_task",
        f"Inspect task (ID: {task_id})",
        full_page=False,
    )


# async def screenshot_inspect_synapse(page, synapse_id=SYNAPSE_ID):
#     """Capture the inspect synapse page."""
#     print(f"\n--- Inspect Synapse Page (ID: {synapse_id}) ---")
#     await page.goto(f"{BASE_URL}/inspect-synapse/{synapse_id}/")
#     await page.wait_for_selector(".inspect-synapse-container", timeout=10000)
#     await take_screenshot(page, "07_inspect_synapse", f"Inspect synapse (ID: {synapse_id})")


async def screenshot_neuroglancer_preferences(page):
    """Capture the neuroglancer preferences panel."""
    print("\n--- Neuroglancer Preferences Panel ---")
    await page.goto(f"{BASE_URL}/preferences/")

    try:
        # Try to find and click neuroglancer preferences
        ng_prefs = await page.query_selector('text="Neuroglancer"')
        if ng_prefs:
            await ng_prefs.click()
            await page.wait_for_timeout(500)
    except:
        print("  Note: Could not find neuroglancer preferences panel")

    await take_screenshot(
        page, "08_neuroglancer_preferences", "Neuroglancer preferences"
    )


async def main():
    """Capture screenshots and update the getting-started document."""
    print("=" * 60)
    print("Neuvue Getting Started Screenshot Updater")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Username: {DOCUMENTATION_USERNAME}")
    print(f"Namespace: {DOCUMENTATION_NAMESPACE}")
    print(f"Task ID: {DOCUMENTATION_TASK_ID}")
    print(f"Chrome profile: {CHROME_PROFILE_DIR.absolute()}")
    print(f"Screenshots: {SCREENSHOTS_DIR.absolute()}")
    print(f"Markdown: {GETTING_STARTED_PATH}")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")

        if not browser.contexts:
            raise RuntimeError("Chrome is running, but no browser context was found.")

        context = browser.contexts[0]

        page = context.pages[0] if context.pages else await context.new_page()

        try:
            await login(page)

            await screenshot_main_landing_page(page)
            await screenshot_tasks_page(page)
            await screenshot_pending_tasks_panel(page, DOCUMENTATION_NAMESPACE)
            await screenshot_closed_tasks_panel(page, DOCUMENTATION_NAMESPACE)
            await screenshot_workspace_page(page, DOCUMENTATION_NAMESPACE)
            await screenshot_inspect_task(
                page,
                DOCUMENTATION_TASK_ID,
                DOCUMENTATION_NAMESPACE,
            )
            await screenshot_neuroglancer_preferences(page)

            print("\n" + "=" * 60)
            print("✓ All screenshots captured!")
            print("=" * 60)

        except Exception as exc:
            print(f"\n✗ Error during screenshot capture: {exc}")
            raise

        finally:
            await browser.close()

    try:
        copy_screenshots_to_static()
        update_markdown()

        print("\n" + "=" * 60)
        print("✓ Successfully updated getting_started.md!")
        print(f"Screenshots: {STATIC_SCREENSHOTS_DIR.absolute()}")
        print("=" * 60)

    except Exception as exc:
        print(f"\n✗ Error during markdown update: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
