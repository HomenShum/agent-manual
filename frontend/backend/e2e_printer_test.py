"""End-to-end browser test: upload printer image → pipeline → manual → chat → Snaplii.

Uses the backend stub frontend at http://127.0.0.1:8102 which is the
Agent Visual Manual system with Snaplii integration.
"""
import asyncio
import os
import sys

from playwright.async_api import async_playwright

FRONTEND = "http://127.0.0.1:8102"
PRINTER_IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "printer.jpg")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e2e_printer_output")
os.makedirs(OUT_DIR, exist_ok=True)


async def run():
    if not os.path.exists(PRINTER_IMG):
        print(f"ERROR: printer.jpg not found at {PRINTER_IMG}")
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 820},
            record_video_dir=OUT_DIR,
            record_video_size={"width": 1280, "height": 820},
        )
        page = await context.new_page()

        console_msgs = []
        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))

        # Step 1: Load the backend stub frontend
        print("Step 1: Loading Agent Visual Manual frontend...")
        await page.goto(FRONTEND, wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=os.path.join(OUT_DIR, "01_homepage.png"))
        print("  Screenshot: 01_homepage.png")

        # Step 2: Upload printer image
        print("Step 2: Uploading printer image...")
        file_input = page.locator("#fileInput")
        await file_input.set_input_files(PRINTER_IMG)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=os.path.join(OUT_DIR, "02a_preview.png"))
        print("  Screenshot: 02a_preview.png")

        # Click Generate button
        run_btn = page.locator("#runBtn")
        await run_btn.click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(OUT_DIR, "02b_generating.png"))
        print("  Screenshot: 02b_generating.png")

        # Step 3: Wait for pipeline to complete (parts + search + manual)
        print("Step 3: Waiting for pipeline (parts breakdown + search + manual generation)...")
        gen_done = False
        for i in range(180):
            await page.wait_for_timeout(2000)
            # The stub frontend shows status text — check for completion
            status_el = page.locator("#statusText")
            if await status_el.count() > 0:
                status_text = await status_el.first.text_content()
                if status_text and ("done" in status_text.lower() or "complete" in status_text.lower()):
                    print(f"  Pipeline complete after ~{(i+1)*2}s")
                    gen_done = True
                    break
                if status_text and "error" in status_text.lower():
                    print(f"  Pipeline ERROR after ~{(i+1)*2}s: {status_text[:100]}")
                    break
                if i % 10 == 0:
                    print(f"  Status: {status_text[:80] if status_text else 'N/A'} ({(i+1)*2}s)")
            else:
                # Check if manual iframe appeared (indicates completion)
                manual_frame = page.locator("#manualFrame, iframe")
                if await manual_frame.count() > 0 and i > 2:
                    print(f"  Manual iframe appeared after ~{(i+1)*2}s")
                    gen_done = True
                    break
                if i % 10 == 0:
                    print(f"  Still waiting... ({(i+1)*2}s)")
        else:
            print("  TIMEOUT: Pipeline did not complete in 360s")

        await page.screenshot(path=os.path.join(OUT_DIR, "03_loaded.png"))
        print("  Screenshot: 03_loaded.png")

        # Step 4: Check for Snaplii cards
        print("Step 4: Checking for Snaplii action cards...")
        await page.wait_for_timeout(3000)
        snaplii = page.locator(".snaplii-section, .snaplii-card")
        if await snaplii.count() > 0:
            card_count = await page.locator(".snaplii-card").count()
            print(f"  Snaplii cards visible: {card_count}")
        else:
            print("  Snaplii section not visible yet")
        await page.screenshot(path=os.path.join(OUT_DIR, "04_snaplii.png"))
        print("  Screenshot: 04_snaplii.png")

        # Step 5: Chat about parts
        print("Step 5: Chatting about parts...")
        ask_input = page.locator("#askInput")
        if await ask_input.count() > 0:
            await ask_input.click()
            await ask_input.fill("What parts can you identify in this printer?")
            await page.wait_for_timeout(500)
            # Click ask button
            ask_btn = page.locator("button:has-text('Ask')")
            if await ask_btn.count() > 0:
                await ask_btn.click()
            else:
                await page.keyboard.press("Enter")
            await page.wait_for_timeout(5000)
            await page.screenshot(path=os.path.join(OUT_DIR, "05_chat_response.png"))
            print("  Screenshot: 05_chat_response.png")
        else:
            print("  No chat input found")
            await page.screenshot(path=os.path.join(OUT_DIR, "05_no_chat.png"))

        # Step 6: Click Snaplii action button
        print("Step 6: Clicking Snaplii action...")
        snaplii_btn = page.locator(".snaplii-card-btn").first
        if await snaplii_btn.count() > 0:
            dialog_messages = []
            async def handle_dialog(dialog):
                dialog_messages.append(dialog.message)
                await dialog.dismiss()
            page.on("dialog", handle_dialog)

            await snaplii_btn.click()
            await page.wait_for_timeout(2000)
            if dialog_messages:
                print(f"  Dialog: {dialog_messages[0][:150]}")
            await page.screenshot(path=os.path.join(OUT_DIR, "06_snaplii_clicked.png"))
            print("  Screenshot: 06_snaplii_clicked.png")
        else:
            print("  No Snaplii button found")
            await page.screenshot(path=os.path.join(OUT_DIR, "06_no_snaplii.png"))

        # Final
        print("Step 7: Final screenshot...")
        await page.screenshot(path=os.path.join(OUT_DIR, "07_final.png"))
        print("  Screenshot: 07_final.png")

        # Print console errors
        errors = [m for m in console_msgs if m.startswith("[error]")]
        if errors:
            print(f"\nConsole errors ({len(errors)}):")
            for e in errors[:5]:
                print(f"  {e[:200]}")

        await context.close()
        await browser.close()

        videos = [f for f in os.listdir(OUT_DIR) if f.endswith(".webm")]
        if videos:
            print(f"\nVideo: {os.path.join(OUT_DIR, videos[0])}")
        screenshots = sorted([f for f in os.listdir(OUT_DIR) if f.endswith(".png")])
        print(f"Screenshots: {len(screenshots)} files in {OUT_DIR}")
        print("\nE2E browser test complete!")


if __name__ == "__main__":
    asyncio.run(run())
