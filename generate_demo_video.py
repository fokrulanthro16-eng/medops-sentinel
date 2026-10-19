"""
MedOps-Sentinel v1.0 - Automated 1080p Video Walkthrough Generator
Uses Playwright + edge-tts + FFmpeg to generate a synchronized high-production
walkthrough of http://127.0.0.1:8000 with professional English voiceover narration.
"""

import asyncio
import glob
import os
import shutil
import subprocess
import time
import edge_tts
import imageio_ffmpeg
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_VIDEO = "medops_sentinel_demo_1080p.mp4"
TEMP_DIR = "temp_recording"
VOICE = "en-US-ChristopherNeural"
RATE = "+8%"

SCENES_NARRATION = [
    # Scene 1: Introduction, Aelion Lab 3D DNA Helix & ICU Telemetry (~30s)
    (
        "scene_1.mp3",
        """Welcome to MedOps-Sentinel: an autonomous clinical AI drift firewall, vitals telemetry monitor, and self-healing healthcare DevOps engine developed for HackOctober across DevOps, Health, and AI tracks. Inspired by the architectural aesthetic of Aelion Lab, our platform combines an interactive three-D liquid-crystal DNA double helix with real-time ICU physiological telemetry. Streams including heart rate, oxygen saturation, and blood pressure are monitored with sub-millisecond precision."""
    ),
    # Scene 2: Chaos Engineering, Model Drift & Auto-Rollback (~39s)
    (
        "scene_2.mp3",
        """In critical healthcare, distribution shifts and sensor corruptions can cause AI hallucinations. Navigating to the Chaos controller, let's inject statistical Model Drift. Notice how the Population Stability Index instantly surges past the zero-point-two-five threshold. In under ten milliseconds, our circuit breaker triggers an automatic zero-downtime rollback to the Safe Fallback engine, shifting the three-D DNA helix to alert crimson. When a lethal dosage attack is attempted, our pharmacological guardrail intercepts the payload with a zero percent unsafe pass-through rate. With the fault cleared, our canary controller restores primary inference."""
    ),
    # Scene 3: HIPAA PHI Redaction Shield & Hugging Face Qwen-72B Dual Copilot (~35s)
    (
        "scene_3.mp3",
        """Next, let's observe our HIPAA PHI shield and clinical AI copilot. Loading the Sepsis Crisis Demo, we dispatch an evaluation. Instantly, our HIPAA shield scrubs protected health information—stripping names, Social Security numbers, and MRNs before model transmission. Concurrently, our Hugging Face Qwen seventy-two B Instruct copilot synthesizes a clinical SBAR handoff summary for doctors, and a DevOps drift root-cause analysis for site reliability engineers. MedOps-Sentinel brings enterprise self-healing resilience and safety to clinical AI."""
    ),
]

def get_audio_duration(file_path: str, ffmpeg_exe: str) -> float:
    cmd = [ffmpeg_exe, "-i", file_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 0.0

async def generate_narration_audio(ffmpeg_exe: str):
    durations = []
    print("Generating voiceover audio narration with edge-tts...")
    for fn, text in SCENES_NARRATION:
        p = os.path.join(TEMP_DIR, fn)
        if not os.path.exists(p):
            comm = edge_tts.Communicate(text, VOICE, rate=RATE)
            await comm.save(p)
        dur = get_audio_duration(p, ffmpeg_exe)
        durations.append(dur)
        print(f"  - {fn}: {dur:.2f}s")
    
    # Concat all 3 audio files into a single master audio track
    concat_list = os.path.join(TEMP_DIR, "concat_list.txt")
    master_audio = os.path.join(TEMP_DIR, "master_audio.mp3")
    with open(concat_list, "w", encoding="utf-8") as f:
        for fn, _ in SCENES_NARRATION:
            p = os.path.abspath(os.path.join(TEMP_DIR, fn)).replace("\\", "/")
            f.write(f"file '{p}'\n")
    
    subprocess.run(
        [ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", master_audio],
        check=True,
        capture_output=True
    )
    total_audio_dur = get_audio_duration(master_audio, ffmpeg_exe)
    print(f"Master voiceover generated: {total_audio_dur:.2f}s")
    return durations, master_audio, total_audio_dur

# Visual Cursor Injection script to display mouse movements & clicks clearly
CURSOR_INJECTION_SCRIPT = """
(() => {
    if (document.getElementById('virtual-cursor')) return;
    const cursor = document.createElement('div');
    cursor.id = 'virtual-cursor';
    cursor.style.position = 'fixed';
    cursor.style.width = '22px';
    cursor.style.height = '22px';
    cursor.style.borderRadius = '50%';
    cursor.style.backgroundColor = 'rgba(43, 76, 126, 0.45)';
    cursor.style.border = '2px solid #2B4C7E';
    cursor.style.boxShadow = '0 0 14px rgba(43, 76, 126, 0.7)';
    cursor.style.pointerEvents = 'none';
    cursor.style.zIndex = '999999';
    cursor.style.transition = 'transform 0.08s ease-out, background-color 0.15s ease';
    cursor.style.transform = 'translate(-50%, -50%)';
    cursor.style.left = '960px';
    cursor.style.top = '540px';
    document.body.appendChild(cursor);

    const dot = document.createElement('div');
    dot.style.position = 'absolute';
    dot.style.width = '6px';
    dot.style.height = '6px';
    dot.style.borderRadius = '50%';
    dot.style.backgroundColor = '#2B4C7E';
    dot.style.top = '50%';
    dot.style.left = '50%';
    dot.style.transform = 'translate(-50%, -50%)';
    cursor.appendChild(dot);

    window.updateVirtualCursor = (x, y) => {
        cursor.style.left = x + 'px';
        cursor.style.top = y + 'px';
    };

    window.triggerCursorClick = () => {
        cursor.style.transform = 'translate(-50%, -50%) scale(0.7)';
        cursor.style.backgroundColor = 'rgba(239, 68, 68, 0.8)';
        cursor.style.borderColor = '#dc2626';
        setTimeout(() => {
            cursor.style.transform = 'translate(-50%, -50%) scale(1)';
            cursor.style.backgroundColor = 'rgba(43, 76, 126, 0.45)';
            cursor.style.borderColor = '#2B4C7E';
        }, 180);
    };

    document.addEventListener('mousemove', (e) => {
        window.updateVirtualCursor(e.clientX, e.clientY);
    });
})();
"""

async def smooth_move_mouse(page, start_x, start_y, end_x, end_y, steps=20, delay_per_step=0.015):
    for i in range(1, steps + 1):
        cur_x = start_x + (end_x - start_x) * (i / steps)
        cur_y = start_y + (end_y - start_y) * (i / steps)
        await page.mouse.move(cur_x, cur_y)
        await page.evaluate(f"window.updateVirtualCursor && window.updateVirtualCursor({cur_x}, {cur_y});")
        await asyncio.sleep(delay_per_step)

async def click_with_visual(page, selector):
    box = await page.locator(selector).bounding_box()
    if box:
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        await page.mouse.move(cx, cy)
        await page.evaluate(f"window.updateVirtualCursor && window.updateVirtualCursor({cx}, {cy});")
        await page.evaluate("window.triggerCursorClick && window.triggerCursorClick();")
        await page.click(selector)
        await asyncio.sleep(0.3)

async def record_playwright_walkthrough(durations, temp_video_dir):
    d1, d2, d3 = durations
    print(f"Starting Playwright browser recording (Scenes: {d1:.1f}s, {d2:.1f}s, {d3:.1f}s)...")
    
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
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=temp_video_dir,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        # Navigate to Dashboard
        t0 = time.time()
        await page.goto(BASE_URL, wait_until="networkidle")
        await page.evaluate(CURSOR_INJECTION_SCRIPT)
        await asyncio.sleep(1.0)

        # ==============================================================
        # SCENE 1: Aelion Lab 3D DNA Hero & Live ICU Signals
        # ==============================================================
        print("Executing Scene 1 choreography (Hero & ICU Vitals Telemetry)...")
        s1_start = time.time()

        # Move mouse across Hero brand and slot status
        await smooth_move_mouse(page, 960, 540, 320, 260, steps=25)
        await asyncio.sleep(1.5)
        
        # Hover over 3D DNA Canvas and gently rotate/inspect
        await smooth_move_mouse(page, 320, 260, 960, 380, steps=25)
        # Interactive drag on canvas
        await page.mouse.down()
        await page.mouse.move(990, 390, steps=10)
        await page.mouse.up()
        await asyncio.sleep(2.0)

        # Move to the microscope tour card
        await smooth_move_mouse(page, 960, 380, 1550, 280, steps=25)
        await asyncio.sleep(2.0)

        # Smooth scroll down to #telemetry
        await page.evaluate("window.scrollTo({top: 780, behavior: 'smooth'});")
        await asyncio.sleep(1.8)

        # Hover over vitals telemetry cards
        # HR
        await smooth_move_mouse(page, 1550, 280, 260, 360, steps=20)
        await asyncio.sleep(2.0)
        # SpO2
        await smooth_move_mouse(page, 260, 360, 520, 360, steps=20)
        await asyncio.sleep(2.0)
        # BP
        await smooth_move_mouse(page, 520, 360, 780, 360, steps=20)
        await asyncio.sleep(2.0)
        # MEWS Radar
        await smooth_move_mouse(page, 780, 360, 1300, 360, steps=25)
        await asyncio.sleep(2.0)
        # Model Drift PSI Gauge
        await smooth_move_mouse(page, 1300, 360, 1600, 360, steps=25)
        await asyncio.sleep(2.5)

        # Pad remaining time of Scene 1
        elapsed_s1 = time.time() - s1_start
        if elapsed_s1 < d1:
            await asyncio.sleep(d1 - elapsed_s1)

        # ==============================================================
        # SCENE 2: Chaos Engineering, Model Drift & Sub-10ms Auto-Rollback
        # ==============================================================
        print("Executing Scene 2 choreography (Chaos SRE & Auto-Rollback)...")
        s2_start = time.time()

        # Smooth scroll down to #chaos
        await page.evaluate("document.getElementById('chaos').scrollIntoView({behavior: 'smooth', block: 'center'});")
        await asyncio.sleep(2.0)

        # Move to 'Inject Model Drift' button
        drift_btn = "button:has-text('Inject Model Drift')"
        await smooth_move_mouse(page, 1600, 360, 300, 520, steps=25)
        await asyncio.sleep(1.0)
        print("  -> Triggering Model Drift fault injection...")
        await click_with_visual(page, drift_btn)
        
        # Wait for PSI surge & instant auto-rollback
        await asyncio.sleep(4.0)

        # Scroll slightly up to show the rollback alert banner and crimson DNA helix
        await page.evaluate("window.scrollBy({top: -300, behavior: 'smooth'});")
        await asyncio.sleep(3.0)

        # Scroll back to chaos grid
        await page.evaluate("document.getElementById('chaos').scrollIntoView({behavior: 'smooth', block: 'center'});")
        await asyncio.sleep(1.5)

        # Move to 'Lethal Dosage Attack' button
        dosage_btn = "button:has-text('Lethal Dosage Attack')"
        print("  -> Triggering Lethal Dosage Attack guardrail test...")
        await click_with_visual(page, dosage_btn)
        await asyncio.sleep(4.0)

        # Move to 'Restore Canary Slot' button to demonstrate self-healing
        restore_btn = "button:has-text('Restore Canary Slot')"
        print("  -> Restoring Primary-AI-Canary slot (self-healing)...")
        await click_with_visual(page, restore_btn)
        await asyncio.sleep(3.5)

        # Pad remaining time of Scene 2
        elapsed_s2 = time.time() - s2_start
        if elapsed_s2 < d2:
            await asyncio.sleep(d2 - elapsed_s2)

        # ==============================================================
        # SCENE 3: HIPAA PHI Redaction Shield & Hugging Face Dual Copilot
        # ==============================================================
        print("Executing Scene 3 choreography (HIPAA Shield & Hugging Face Qwen-72B)...")
        s3_start = time.time()

        # Smooth scroll to #copilot
        await page.evaluate("document.getElementById('copilot').scrollIntoView({behavior: 'smooth', block: 'start'});")
        await asyncio.sleep(2.0)

        # Move to '[Load Sepsis Crisis Demo]' button
        demo_btn = "button:has-text('[Load Sepsis Crisis Demo]')"
        print("  -> Loading Sepsis Crisis Demo preset...")
        await click_with_visual(page, demo_btn)
        await asyncio.sleep(2.0)

        # Move mouse to highlight the clinical note with PII/PHI
        notes_box = "#inputNotes"
        box = await page.locator(notes_box).bounding_box()
        if box:
            await smooth_move_mouse(page, 960, 300, box["x"] + 150, box["y"] + 30, steps=20)
            await asyncio.sleep(1.5)

        # Move to 'Run Clinical Evaluation & AI Analysis' submit button
        submit_btn = "button[type='submit']"
        print("  -> Dispatching Clinical Evaluation & AI Guardrail Audit...")
        await click_with_visual(page, submit_btn)
        await asyncio.sleep(3.0)

        # Move to and highlight the Scrubbed Clinical Note (sent to AI)
        redacted_box = "#evalRedactedNotes"
        r_box = await page.locator(redacted_box).bounding_box()
        if r_box:
            await smooth_move_mouse(page, 500, 700, r_box["x"] + 120, r_box["y"] + 25, steps=20)
            await asyncio.sleep(2.5)

        # Move to Guardrail Decision banner (0.0% Lethal pass-through)
        guard_banner = "#guardrailBanner"
        g_box = await page.locator(guard_banner).bounding_box()
        if g_box:
            await smooth_move_mouse(page, 500, 500, g_box["x"] + 120, g_box["y"] + 25, steps=20)
            await asyncio.sleep(2.5)

        # Move to Hugging Face Qwen-72B Dual Reports
        # SBAR Summary Card
        sbar_card = "#hfSbarText"
        s_box = await page.locator(sbar_card).bounding_box()
        if s_box:
            await smooth_move_mouse(page, 500, 500, s_box["x"] + 150, s_box["y"] + 40, steps=25)
            await asyncio.sleep(3.0)

        # DevOps Drift RCA Card
        rca_card = "#hfRcaText"
        rca_box = await page.locator(rca_card).bounding_box()
        if rca_box:
            await smooth_move_mouse(page, s_box["x"] + 150, s_box["y"] + 40, rca_box["x"] + 150, rca_box["y"] + 40, steps=25)
            await asyncio.sleep(3.0)

        # Smooth scroll back up to the monumental Hero section with DNA helix
        await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'});")
        await asyncio.sleep(2.5)

        # Pad remaining time of Scene 3
        elapsed_s3 = time.time() - s3_start
        if elapsed_s3 < d3:
            await asyncio.sleep(d3 - elapsed_s3)

        print(f"Total recording time: {time.time() - t0:.2f}s")
        await context.close()
        await browser.close()

async def mux_video_and_audio(temp_video_dir: str, master_audio: str, ffmpeg_exe: str):
    print("Muxing final 1080p video with synchronized audio narration...")
    webm_files = glob.glob(os.path.join(temp_video_dir, "*.webm"))
    if not webm_files:
        raise RuntimeError("No Playwright WebM video recorded!")
    raw_webm = webm_files[0]
    print(f"Raw recorded video: {raw_webm} ({os.path.getsize(raw_webm)} bytes)")

    # FFmpeg command: transcode WebM to pristine H.264 MP4 with AAC audio
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", raw_webm,
        "-i", master_audio,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUTPUT_VIDEO
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        raise RuntimeError("FFmpeg muxing failed")

    out_size = os.path.getsize(OUTPUT_VIDEO)
    out_dur = get_audio_duration(OUTPUT_VIDEO, ffmpeg_exe)
    print("\n============================================================")
    print("DEMO VIDEO GENERATION COMPLETE!")
    print(f"Output File:     {os.path.abspath(OUTPUT_VIDEO)}")
    print(f"File Size:       {out_size / (1024 * 1024):.2f} MB")
    print(f"Duration:        {out_dur:.2f} seconds")
    print(f"Resolution:      1920x1080 (1080p 30fps Full HD)")
    print("============================================================\n")

async def main():
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_video_dir = os.path.join(TEMP_DIR, "raw_video")
    os.makedirs(temp_video_dir, exist_ok=True)
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    durations, master_audio, total_dur = await generate_narration_audio(ffmpeg_exe)
    
    await record_playwright_walkthrough(durations, temp_video_dir)
    await mux_video_and_audio(temp_video_dir, master_audio, ffmpeg_exe)

if __name__ == "__main__":
    asyncio.run(main())
