#!/usr/bin/env python3
"""
Screenshot updater for Neuvue getting started documentation.
Automatically captures screenshots of key pages for documentation and updates
the getting_started.md file with new screenshot references.

Usage:
    python screenshot_updater.py

Environment variables:
    NEUVUE_URL - Base URL (default: http://localhost:8000)
    NAMESPACE - Namespace to capture
    TASK_ID - Task ID to inspect
    SYNAPSE_ID - Synapse ID to inspect
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
USERNAME = "dxenes1"
PASSWORD = "temptest123"

# Define variables for task/synapse IDs and namespace
NAMESPACE = os.environ.get("NAMESPACE", "v1dd_split_validation_hc")
TASK_ID = os.environ.get("TASK_ID", "69ed038caf31f6146ab16a15")
# SYNAPSE_ID = os.environ.get("SYNAPSE_ID", "1")

# Paths
PROJECT_ROOT = Path(__file__).parent
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
STATIC_DIR = PROJECT_ROOT / "neuvue_project" / "workspace" / "static"
STATIC_SCREENSHOTS_DIR = STATIC_DIR / "screenshots"
GETTING_STARTED_PATH = STATIC_DIR / "getting_started.md"

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
    await page.goto(
        f"{BASE_URL}/accounts/login/",
        wait_until="domcontentloaded",
    )

    print("Login URL:", page.url)
    print("Login title:", await page.title())

    username_input = page.locator("#id_login")
    password_input = page.locator("#id_password")

    await username_input.wait_for(state="visible", timeout=30_000)
    await username_input.fill(USERNAME)
    await password_input.fill(PASSWORD)

    async with page.expect_navigation(wait_until="domcontentloaded"):
        await page.get_by_role("button", name="Sign In").click()

    print("After login URL:", page.url)


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


async def take_screenshot(page, name, description=""):
    """Capture a screenshot after collapsing the Django Debug Toolbar."""
    filename = SCREENSHOTS_DIR / f"{name}.png"

    await collapse_django_debug_toolbar(page)

    await page.screenshot(
        path=str(filename),
        full_page=True,
    )

    print(f"  ✓ {description or name} → {filename}")
    return filename


async def screenshot_main_landing_page(page):
    """Capture main landing page while logged in."""
    print("\n--- Main Landing Page (Logged In) ---")
    await page.goto(f"{BASE_URL}/")
    await page.wait_for_load_state("networkidle")
    await take_screenshot(page, "01_main_landing_page", "Main landing page")


async def screenshot_tasks_page(page):
    """Capture the Tasks page."""
    print("\n--- Tasks Page ---")

    response = await page.goto(
        f"{BASE_URL}/tasks/",
        wait_until="domcontentloaded",
    )

    print("Status:", response.status if response else None)
    print("Current URL:", page.url)

    await page.locator(".tasks-container").wait_for(
        state="visible",
        timeout=10_000,
    )

    await take_screenshot(
        page,
        "02_tasks_page",
        "Tasks page",
    )


async def screenshot_pending_tasks_panel(page, namespace=NAMESPACE):
    """Capture the pending tasks panel for a namespace."""
    print(f"\n--- Pending Tasks Panel ({namespace}) ---")

    await page.goto(
        f"{BASE_URL}/tasks/",
        wait_until="domcontentloaded",
    )

    await page.locator(".tasks-container").wait_for(
        state="visible",
        timeout=10_000,
    )

    namespace_header = page.locator(f"#{namespace}Header")
    namespace_table = page.locator(f"#{namespace}Table")
    pending_tab = page.locator(f"#pending{namespace}Tab")
    pending_panel = page.locator(f"#pending{namespace}")

    if await namespace_header.count() == 0:
        raise RuntimeError(
            f"Namespace {namespace!r} was not found on the Tasks page. "
            "The namespace may have zero tasks or may not be available "
            "to the logged-in user."
        )

    await namespace_header.wait_for(
        state="visible",
        timeout=10_000,
    )

    if not await namespace_table.is_visible():
        await namespace_header.click()

    await namespace_table.wait_for(
        state="visible",
        timeout=5_000,
    )

    await pending_tab.click()

    await pending_panel.wait_for(
        state="visible",
        timeout=5_000,
    )

    await take_screenshot(
        page,
        "03_pending_tasks_panel",
        f"Pending tasks ({namespace})",
    )


async def screenshot_closed_tasks_panel(page, namespace=NAMESPACE):
    """Capture the closed-tasks tab for a namespace."""
    print(f"\n--- Closed Tasks Panel ({namespace}) ---")

    response = await page.goto(
        f"{BASE_URL}/tasks/",
        wait_until="domcontentloaded",
    )

    status = response.status if response else None
    if response is None or not response.ok:
        raise RuntimeError(f"Tasks request failed with HTTP {status}: {page.url}")

    tasks_container = page.locator(".tasks-container")
    namespace_header = page.locator(f'[id="{namespace}Header"]')
    namespace_table = page.locator(f'[id="{namespace}Table"]')
    closed_tab = page.locator(f'[id="closed{namespace}Tab"]')
    closed_panel = page.locator(f'[id="closed{namespace}"]')

    await tasks_container.wait_for(
        state="visible",
        timeout=10_000,
    )

    if await namespace_header.count() == 0:
        raise RuntimeError(
            f"Namespace {namespace!r} was not found on the Tasks page. "
            "The namespace may have zero tasks or may not be available "
            "to the logged-in user."
        )

    await namespace_header.wait_for(
        state="visible",
        timeout=10_000,
    )

    # The namespace table is initially hidden with an inline display:none.
    # Click the header and verify that the table actually opens.
    if not await namespace_table.is_visible():
        await namespace_header.click()

        await page.wait_for_function(
            """table_id => {
                const table = document.getElementById(table_id);
                return table && window.getComputedStyle(table).display !== "none";
            }""",
            f"{namespace}Table",
            timeout=5_000,
        )

    await closed_tab.wait_for(
        state="visible",
        timeout=5_000,
    )

    # Use the element's native click so its inline tabToggle handler runs.
    await closed_tab.evaluate("(element) => element.click()")

    # Verify both the panel state and selected-tab state before capturing.
    await page.wait_for_function(
        """({ panel_id, tab_id }) => {
            const panel = document.getElementById(panel_id);
            const tab = document.getElementById(tab_id);

            return (
                panel &&
                tab &&
                window.getComputedStyle(panel).display !== "none" &&
                tab.classList.contains("active")
            );
        }""",
        {
            "panel_id": f"closed{namespace}",
            "tab_id": f"closed{namespace}Tab",
        },
        timeout=5_000,
    )

    await closed_panel.scroll_into_view_if_needed()

    await take_screenshot(
        page,
        "04_closed_tasks_panel",
        f"Closed tasks ({namespace})",
    )


async def screenshot_workspace_page(page, namespace=NAMESPACE):
    """Capture the Workspace page."""
    print(f"\n--- Workspace Page ({namespace}) ---")

    response = await page.goto(
        f"{BASE_URL}/workspace/{namespace}",
        wait_until="domcontentloaded",
    )

    status = response.status if response else None
    print("Status:", status)
    print("Current URL:", page.url)

    if response is None or not response.ok:
        raise RuntimeError(f"Workspace request failed with HTTP {status}: {page.url}")

    await page.locator(".workspace-container").wait_for(
        state="visible",
        timeout=10_000,
    )

    await take_screenshot(
        page,
        "05_workspace_page",
        f"Workspace page ({namespace})",
    )


async def screenshot_inspect_task(page, task_id=TASK_ID):
    """Capture the inspect task page."""
    print(f"\n--- Inspect Task Page (ID: {task_id}) ---")

    response = await page.goto(
        f"{BASE_URL}/inspect/{task_id}",
        wait_until="domcontentloaded",
    )

    status = response.status if response else None
    print("Status:", status)
    print("Current URL:", page.url)

    if response is None or not response.ok:
        raise RuntimeError(
            f"Inspect task request failed with HTTP {status}: {page.url}"
        )

    await page.locator(".inspect-task-container").wait_for(
        state="visible",
        timeout=10_000,
    )

    await take_screenshot(
        page,
        "06_inspect_task",
        f"Inspect task (ID: {task_id})",
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
    """Main function to capture all screenshots and update markdown."""
    print("=" * 60)
    print("Neuvue Getting Started Screenshot Updater")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Username: {USERNAME}")
    print(f"Namespace: {NAMESPACE}")
    print(f"Task ID: {TASK_ID}")
    # print(f"Synapse ID: {SYNAPSE_ID}")
    print(f"Screenshots: {SCREENSHOTS_DIR.absolute()}")
    print(f"Markdown: {GETTING_STARTED_PATH}")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        try:
            await login(page)

            # Capture all screenshots
            await screenshot_main_landing_page(page)
            await screenshot_tasks_page(page)
            await screenshot_pending_tasks_panel(page, NAMESPACE)
            await screenshot_closed_tasks_panel(page, NAMESPACE)
            await screenshot_workspace_page(page, NAMESPACE)
            await screenshot_inspect_task(page, TASK_ID)
            # await screenshot_inspect_synapse(page, SYNAPSE_ID)
            await screenshot_neuroglancer_preferences(page)

            print("\n" + "=" * 60)
            print("✓ All screenshots captured!")
            print("=" * 60)

        except Exception as e:
            print(f"\n✗ Error during screenshot capture: {e}")
            raise
        finally:
            await context.close()
            await browser.close()

    # Post-processing: copy to static and update markdown
    try:
        copy_screenshots_to_static()
        update_markdown()

        print("\n" + "=" * 60)
        print("✓ Successfully updated getting_started.md!")
        print(f"Screenshots: {STATIC_SCREENSHOTS_DIR.absolute()}")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error during markdown update: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
