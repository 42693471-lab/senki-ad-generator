#!/usr/bin/env python3
"""Lovart Batch Tool — lightweight backend with direct API integration."""
import http.server
import json
import os
import sys
import shutil
import time
import urllib.parse
import uuid
import socketserver
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GENERATED = ROOT / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

# Import AgentSkill from local project dir (for portability / cloud deploy)
from agent_skill import AgentSkill, LocalState

AK = os.environ.get("LOVART_ACCESS_KEY", "")
SK = os.environ.get("LOVART_SECRET_KEY", "")
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-ea9723f06e63409ba6ed583c74172393")
if not AK or not SK:
    print("ERROR: LOVART_ACCESS_KEY and LOVART_SECRET_KEY must be set.")
    sys.exit(1)

skill = AgentSkill(base_url="https://lgw.lovart.ai", access_key=AK, secret_key=SK, timeout=600)
state = LocalState()

# Style id → DeepSeek matching keywords
# Style id → DeepSeek matching keywords (8 categories × 8 styles = 64 total)
STYLE_CATEGORIES = {
    # 自然仿生系列 Nature Bio+
    "NB1": "frozen glacial ice, frost, cracked ice, cold blue light, 5600K, hyper-realistic ice block, winter",
    "NB2": "desert sand dunes, golden hour, warm cinematic shadows, sand particles, sunset, warm tones",
    "NB3": "dark volcanic rock, green moss, misty forest, humid, velvet moss, top-down lighting",
    "NB4": "zen water garden, lily pad, water ripples, morning mist, pastel, soft natural light, lotus",
    "NB5": "black basalt, jagged stones, steam, obsidian, rim lighting, dramatic high contrast, dark",
    "NB6": "dewy morning, water drop splash, crown splash, flower petals, bright airy, fresh, high-speed",
    "NB7": "autumn amber, warm wood, maple leaves, bokeh, cozy, Rembrandt lighting, furniture texture",
    "NB8": "pink salt crystals, himalayan salt, translucent, clean white, pure, minimalist, refracted light",
    # 现代建筑系列 Architectural Minimal
    "AR1": "brutalist concrete, raw grey, hard shadows, industrial chic, neutral, minimalist architecture",
    "AR2": "neo-classical archway, plaster texture, terracotta, cream, elegant, spatial depth, arches",
    "AR3": "spiral staircase, curving architecture, dynamic lines, golden ratio, cinematic lighting above",
    "AR4": "carrara marble, dark walnut wood, museum spotlight, luxury retail, high gloss floor",
    "AR5": "white plaster waves, abstract, organic shapes, chiaroscuro, serene calm, soft shadow",
    "AR6": "terrazzo, multi-colored, playful, vibrant, professional, clean, diffused light",
    "AR7": "glass block wall, 90s retro, distorted light, colorful refraction, dreamy blur, soft glow",
    "AR8": "symmetrical concrete steps, sharp geometry, hero shot, high fashion editorial, peak",
    # 光学物理系列 Optical & Physics
    "OP1": "venetian blind shadows, 45-degree light, dust motes, cinematic, warm sun-drenched, storytelling",
    "OP2": "crystal prism, rainbow dispersion, chromatic aberration, ethereal, spectral light, 8k",
    "OP3": "pool caustics, water light patterns, turquoise, summer, wet-look, aquatic reflections",
    "OP4": "dappled sunlight, palm leaves, tropical, warm highlights, organic shadows, vacation mood",
    "OP5": "anamorphic lens flare, horizontal blue flare, sci-fi, dark background, futuristic, cinematic",
    "OP6": "iridescent oil film, swirling rainbow, macro droplets, mesmerizing, creative, polarized",
    "OP7": "rim light noir, pitch black, dual rim lights blue orange, bottle curvature, extreme mystery",
    "OP8": "golden hour glow, 3200K low sun, long shadows, lifestyle editorial, soft skin tones, warm",
    # 实验室科技系列 Scientific Lab
    "SL1": "petri dish, gel texture, microscopic bubbles, sterile white, biotech, scientific glass",
    "SL2": "liquid nitrogen, white fog, frozen metal, cold blue accent, high-tech, ultra-clean, vapor",
    "SL3": "blue laser line, scanning, dark tech, data visualization, cutting-edge, horizontal beam",
    "SL4": "centrifuge motion blur, circular blur, dynamic energy, laboratory speed, sharp product",
    "SL5": "copper steel, industrial lab tubes, brushed metal, steampunk, sophisticated engineering",
    "SL6": "holographic grid, 3D digital projection, cyberpunk UI, neon blue violet, future skin care",
    "SL7": "bubbling beaker, effervescent oxygen bubbles, clear liquid, active ingredient, high-speed shutter",
    "SL8": "silver vacuum, aluminum foil, crinkled texture, metallic reflections, space-age, high-tech packaging",
    # 超现实空间系列 Surrealism
    "SU1": "anti-gravity, zero gravity, floating spheres, white void, perfect symmetry, surreal clean, 8k",
    "SU2": "silk ribbon, floating, wrapping, fluid motion, soft satin, pastel, elegant fabric",
    "SU3": "puffy white clouds, blue sky, dreamlike, air-light, cloud kingdom, soft, heavenly",
    "SU4": "liquid silver, melting mirror, rippling surface, distorted reflections, surreal metal, fluid",
    "SU5": "spheres cubes, marble glass, floating geometric, Bauhaus, avant-garde, balanced composition",
    "SU6": "hallway of mirrors, infinite reflections, recursive, depth of field, optical illusion, infinite room",
    "SU7": "origami paper folds, sharp creases, pure white shadows, minimalist craft, tactile paper",
    "SU8": "soap bubble, iridescent swirls, giant bubble, clean studio, fragile beauty, sphere",
    # 材质特写系列 Texture Macro
    "TM1": "whipped cream swirl, thick luxurious white, macro peaks, edible texture, creamy, soft peaks",
    "TM2": "honey drip, thick amber liquid, backlit viscosity, warm rich, golden, slow drip",
    "TM3": "crushed pigment explosion, colorful eyeshadow powder, sharp grit, vibrant saturated, macro powder",
    "TM4": "burgundy velvet, deep red, light absorbing, heavy luxury, premium tactile, plush fabric",
    "TM5": "smeared lipstick, artful cream smudge, painterly brushstrokes, cosmetic texture, artistic",
    "TM6": "transparent jelly cubes, crystal clear, light passing through, refreshing, hydrating, gel",
    "TM7": "24k gold leaf flakes, floating gold, warm luxury, prestige, gilded, metallic flake",
    "TM8": "carbonated fizz, micro-bubbles clinging, soda freshness, macro clarity, effervescent",
    # 生活方式系列 High-end Lifestyle
    "LS1": "parisian cafe, marble bistro table, croissant espresso, soft morning sun, effortless chic, French",
    "LS2": "silk pillowcase, messy bedding, morning light, intimate cozy, luxury home, soft fabric",
    "LS3": "antique gold mirror, boudoir reflection, soft focus bathroom, romantic, vintage gold",
    "LS4": "private jet, leather tray, window clouds, jet-set travel, ultimate wealth, luxury travel",
    "LS5": "modern bathroom, stone sink, steam, spa atmosphere, minimalist sanctuary, zen",
    "LS6": "glitter table, champagne glass blur, party lights, nightlife, high-glam, celebration",
    "LS7": "canvas tote bag, straw hat, beach sand, outdoor natural light, weekend escape, summer",
    "LS8": "tennis club, white pleats, green court, preppy, clean athletic, sporty luxury",
    # 艺术流派系列 Art History
    "AH1": "vermeer light, single side light, deep shadows, oil painting texture, timeless elegance, Dutch",
    "AH2": "bauhaus primary colors, red blue yellow, geometric blocks, rigid grid, modernist, stark",
    "AH3": "cyberpunk neon, pink cyan, rainy street reflections, futuristic, neon glow, dystopian",
    "AH4": "monet garden, soft blurred impressionist flowers, dappled light, pastel oil strokes, impressionism",
    "AH5": "pop art, high saturation yellow magenta, bold outlines, warhol style, flat color, comic",
    "AH6": "ukiyo-e wave, stylized blue white waves, japanese woodblock, flat graphic, hokusai inspired",
    "AH7": "zen ink wash, negative space, ma aesthetic, subtle grey gradients, spiritual, minimal ink",
    "AH8": "techno-glow, electronic circuit light trails, glowing green white, high-performance tech, PCB",
}


def deepseek_analyze(base64_data: str) -> dict:
    """Call DeepSeek VLM to analyze product image and recommend a style."""
    import urllib.request
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this product photo. Return ONLY a JSON object:\n- category: product type (Skincare/Fragrance/Cosmetics/Tech/Other)\n- material: packaging material (Glass/Matte Plastic/Glossy Plastic/Metal/Paper)\n- dominantColor: main color hex\n- matchStyle: best matching STYLE PREFIX from these 8:\n  NB = Nature Bio (ice/desert/moss/water/rock/dew/autumn/salt - organic natural freshness)\n  AR = Architectural (concrete/arch/marble/plaster/terrazzo/glass/stairs - structural minimal)\n  OP = Optical (blinds/prism/caustics/palm/anamorphic/oil/rim/golden - light & shadow)\n  SL = Science Lab (petri/nitrogen/laser/centrifuge/copper/hologram/beaker/silver - biotech)\n  SU = Surrealism (gravity/ribbon/cloud/mirror/geometric/infinite/origami/bubble - dreamlike)\n  TM = Texture Macro (cream/honey/pigment/velvet/smear/jelly/gold/fizz - tactile close-up)\n  LS = Lifestyle (cafe/silk/mirror/jet/spa/party/tote/tennis - high-end living scenes)\n  AH = Art History (vermeer/bauhaus/cyberpunk/monet/popart/ukiyoe/ink/techno - artistic styles)\nReturn: {\"category\":\"...\", \"material\":\"...\", \"dominantColor\":\"#...\", \"matchStyle\":\"NB\"}"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64_data}},
            ],
        }],
        "response_format": {"type": "json_object"},
        "max_tokens": 256,
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {DS_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


def download_url(url: str, prefix: str = "lovart") -> str:
    """Download a single URL to generated dir, return relative path."""
    import urllib.request
    ext = os.path.splitext(url.split("?")[0])[-1] or ".png"
    fname = f"{prefix}_{uuid.uuid4().hex[:8]}{ext}"
    dest = GENERATED / fname
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.lovart.ai/",
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.write_bytes(resp.read())
        return str(dest.relative_to(ROOT))
    except Exception:
        return None


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # ── routing ──────────────────────────────────────────────────

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/config":
            data = state.load()
            active = data.get("active_project", "")
            projects = data.get("projects", {})
            threads = data.get("threads", [])
            return self._json({
                "active_project": active,
                "projects": projects,
                "threads": threads,
            })
        if path == "/api/mode":
            return self._json(skill.query_mode())
        if path.startswith("/generated/"):
            return super().do_GET()
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/upload":
            return self._handle_upload()
        body_raw = self._read_body()
        body = json.loads(body_raw) if body_raw else {}
        if path == "/api/generate":
            return self._handle_generate(body)
        if path == "/api/analyze":
            return self._handle_analyze(body)
        if path == "/api/poll":
            return self._handle_poll(body)
        if path == "/api/set-mode":
            if body.get("mode") == "fast":
                skill.set_mode(unlimited=False)
            else:
                skill.set_mode(unlimited=True)
            return self._json(skill.query_mode())
        self.send_response(404)
        self.end_headers()

    # ── helpers ───────────────────────────────────────────────────

    def _read_body(self) -> str:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode("utf-8") if length else ""

    def _json(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def end_headers(self):
        # Disable caching for all responses so frontend always gets latest
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle_upload(self):
        """Handle multipart file upload → CDN."""
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_response(400)
            self.end_headers()
            return
        boundary = content_type.split("boundary=")[1].strip()
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        b = boundary.encode()
        marker = b"--" + b
        parts = raw.split(marker)
        for part in parts[1:]:
            if b"filename=" in part:
                header_end = part.find(b"\r\n\r\n")
                if header_end < 0:
                    continue
                file_data = part[header_end + 4:]
                end_marker = file_data.rfind(b"\r\n" + marker)
                if end_marker < 0:
                    end_marker = file_data.rfind(b"\r\n--" + b + b"--")
                if end_marker >= 0:
                    file_data = file_data[:end_marker]
                file_data = file_data.rstrip(b"\r\n-")
                tmp = GENERATED / f"upload_{uuid.uuid4().hex[:8]}.jpg"
                tmp.write_bytes(file_data)
                try:
                    url = skill.upload_file(str(tmp))
                except Exception as e:
                    url = None
                tmp.unlink(missing_ok=True)
                if url:
                    return self._json({"url": url})
                return self._json({"error": True, "message": "Upload failed"})
        self.send_response(400)
        self.end_headers()

    def _handle_analyze(self, body: dict):
        """DeepSeek VLM analysis → recommend best matching style."""
        image = body.get("image", "")
        if not image:
            return self._json({"error": True, "message": "Image required"})
        base64_data = image.split(",", 1)[-1] if "," in image else image
        try:
            result = deepseek_analyze(base64_data)
            # Map category prefix to first style in that category
            prefix = result.get("matchStyle", "NB")
            category_first = {
                "NB": "NB1", "AR": "AR1", "OP": "OP1", "SL": "SL1",
                "SU": "SU1", "TM": "TM1", "LS": "LS1", "AH": "AH1",
            }
            result["matchStyle"] = category_first.get(prefix, "NB1")
            return self._json(result)
        except Exception as e:
            print(f"[analyze] DeepSeek error: {e}", flush=True)
            return self._json({"error": True, "message": str(e)})

    def _handle_generate(self, body: dict):
        """Send prompt (non-blocking) → return thread_id immediately. Client polls /api/poll."""
        prompt = body.get("prompt", "")
        attachments = body.get("attachments", [])
        mode = body.get("mode", "fast")
        project_id = state.get_project_id()

        if not project_id:
            try:
                project_id = skill.create_project()
                state.add_project(project_id, prompt[:30].strip())
            except Exception as e:
                return self._json({"error": True, "message": str(e)})

        try:
            tid = skill.send(
                prompt=prompt,
                project_id=project_id,
                attachments=attachments if attachments else None,
                mode=mode,
                prefer_models={"IMAGE": ["generate_image_nano_banana_2"]},
            )
            state.upsert_thread(tid, prompt[:50].strip())
            print(f"[send] thread={tid[:16]}...", flush=True)
            return self._json({"thread_id": tid, "status": "running"})
        except Exception as e:
            msg = str(e)
            return self._json({"error": True, "message": msg})

    def _handle_poll(self, body: dict):
        """Poll thread result, download artifacts when ready."""
        tid = body.get("thread_id", "")
        try:
            result = skill.get_result(tid)
        except Exception:
            return self._json({"thread_id": tid, "status": "unknown", "downloaded": []})

        items = result.get("items", [])
        downloaded = []
        for item in items:
            for a in item.get("artifacts", []):
                url = a.get("content", "")
                if url:
                    local = download_url(url)
                    if local:
                        downloaded.append({"url": url, "local_path": local})

        if downloaded:
            return self._json({"thread_id": tid, "status": "done", "downloaded": downloaded})

        # Check status
        try:
            st = skill.get_status(tid)
            return self._json({"thread_id": tid, "status": st.get("status", "running"), "downloaded": []})
        except Exception:
            return self._json({"thread_id": tid, "status": "running", "downloaded": []})


def main():
    port = int(os.environ.get("PORT", "8766"))
    print(f" Lovart Batch Tool → http://localhost:{port}")
    print(f"   Mode: direct API (no subprocess)")
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer(("0.0.0.0", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutdown.")
        server.shutdown()


if __name__ == "__main__":
    main()
