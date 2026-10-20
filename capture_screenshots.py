"""
MedOps-Sentinel v1.0 - Devpost Gallery Screenshot Capturer
Captures 5 high-resolution (1920x1080) PNG screenshots of the Aelion Lab UI,
ICU Telemetry, Chaos Rollback Engine, Hugging Face Copilot, and HIPAA Shield.
"""

import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:8000"
OUTPUT_DIR = "./screenshots"

async def capture_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Capturing 5 high-resolution (1920x1080) screenshots to {OUTPUT_DIR}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--enable-webgl",
                "--use-gl=angle",
                "--enable-gpu-rasterization",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        page = await browser.new_page(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1
        )

        # -------------------------------------------------------------
        # 1. Hero Section & 3D DNA Helix (01_hero_dna_telemetry.png)
        # -------------------------------------------------------------
        print("1. Capturing Hero Section & 3D DNA Helix...")
        await page.goto(BASE_URL, wait_until="networkidle")
        await page.evaluate("window.scrollTo(0, 0);")
        # Allow Three.js WebGL animation and materials to render specular shine
        await asyncio.sleep(2.5)

        hero_path = os.path.join(OUTPUT_DIR, "01_hero_dna_telemetry.png")
        await page.screenshot(path=hero_path)
        print(f"  -> Captured: {hero_path}")

        # -------------------------------------------------------------
        # 2. ICU Vitals Telemetry & MEWS Radar (02_icu_vitals_radar.png)
        # -------------------------------------------------------------
        print("2. Capturing Real-Time ICU Physiological Signals...")
        # Scroll precisely to #workbench section header
        await page.evaluate("""
            const wb = document.getElementById('workbench');
            if (wb) {
                const y = wb.getBoundingClientRect().top + window.scrollY - 30;
                window.scrollTo({ top: y, behavior: 'instant' });
            }
        """)
        await asyncio.sleep(2.0)

        vitals_path = os.path.join(OUTPUT_DIR, "02_icu_vitals_radar.png")
        await page.screenshot(path=vitals_path)
        print(f"  -> Captured: {vitals_path}")

        # -------------------------------------------------------------
        # 3. Chaos Auto-Rollback Engine (03_chaos_auto_rollback.png)
        # -------------------------------------------------------------
        print("3. Triggering Chaos Model Drift & Capturing Auto-Rollback...")
        # Click 'Inject Model Drift'
        drift_btn = page.locator("button:has-text('Inject Model Drift')")
        if await drift_btn.count() > 0:
            await drift_btn.first.click()
            print("  -> Clicked 'Inject Model Drift'.")
        
        # Wait for PSI surge, circuit-breaker rollback, and red/amber alerts
        await asyncio.sleep(2.5)

        # Scroll so that the Metric Cards (with red driftCard) and the Chaos Controller are centered
        await page.evaluate("""
            const card = document.getElementById('driftCard');
            if (card) {
                const y = card.getBoundingClientRect().top + window.scrollY - 100;
                window.scrollTo({ top: y, behavior: 'instant' });
            }
        """)
        await asyncio.sleep(1.0)

        chaos_path = os.path.join(OUTPUT_DIR, "03_chaos_auto_rollback.png")
        await page.screenshot(path=chaos_path)
        print(f"  -> Captured: {chaos_path}")

        # -------------------------------------------------------------
        # 4 & 5. Load Sepsis Crisis Demo and Run Audit
        # -------------------------------------------------------------
        print("4 & 5. Loading Sepsis Crisis Demo & Running AI Audit...")
        # Reset canary for evaluation
        restore_btn = page.locator("button:has-text('Restore Canary Slot')")
        if await restore_btn.count() > 0:
            await restore_btn.first.click()
            await asyncio.sleep(0.8)

        # Scroll to #copilot
        await page.evaluate("""
            const cp = document.getElementById('copilot');
            if (cp) {
                const y = cp.getBoundingClientRect().top + window.scrollY - 70;
                window.scrollTo({ top: y, behavior: 'instant' });
            }
        """)
        await asyncio.sleep(0.8)

        # Load Sepsis Crisis preset
        demo_btn = page.locator("button:has-text('[Load Sepsis Crisis Demo]')")
        if await demo_btn.count() > 0:
            await demo_btn.first.click()
            print("  -> Clicked '[Load Sepsis Crisis Demo]'.")
        await asyncio.sleep(1.0)

        # Submit evaluation
        eval_btn = page.locator("button[type='submit']")
        if await eval_btn.count() > 0:
            await eval_btn.first.click()
            print("  -> Clicked 'Run Clinical Evaluation & AI Analysis'.")

        # Wait for PHI scrub and Hugging Face generation
        await asyncio.sleep(3.0)

        # -------------------------------------------------------------
        # 4. Hugging Face Qwen-72B Dual Copilot View (04_hf_qwen_copilot.png)
        # -------------------------------------------------------------
        print("4. Capturing Hugging Face Qwen-72B Dual Copilot View...")
        await page.evaluate("""
            const cp = document.getElementById('copilot');
            if (cp) {
                const y = cp.getBoundingClientRect().top + window.scrollY - 65;
                window.scrollTo({ top: y, behavior: 'instant' });
            }
        """)
        await asyncio.sleep(1.0)

        copilot_path = os.path.join(OUTPUT_DIR, "04_hf_qwen_copilot.png")
        await page.screenshot(path=copilot_path)
        print(f"  -> Captured: {copilot_path}")

        # -------------------------------------------------------------
        # 5. HIPAA PHI Redaction Shield View (05_phi_redaction_shield.png)
        # -------------------------------------------------------------
        print("5. Capturing HIPAA PHI Redaction Shield View...")
        # Scroll to cleanly frame the HIPAA Workbench, Scrubbed Notes, and Guardrail Interception
        await page.evaluate("""
            const cp = document.getElementById('copilot');
            if (cp) {
                const y = cp.getBoundingClientRect().top + window.scrollY - 60;
                window.scrollTo({ top: y, behavior: 'instant' });
            }
        """)
        await asyncio.sleep(1.0)

        phi_path = os.path.join(OUTPUT_DIR, "05_phi_redaction_shield.png")
        await page.screenshot(path=phi_path)
        print(f"  -> Captured: {phi_path}")

        await browser.close()

    print("\n=======================================================")
    print("ALL 5 SCREENSHOTS SUCCESSFULLY CAPTURED (1920x1080 PNG):")
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if fname.endswith(".png"):
            fpath = os.path.join(OUTPUT_DIR, fname)
            fsize = os.path.getsize(fpath) / 1024
            print(f"  - {fname}: {fsize:.1f} KB")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(capture_all())
