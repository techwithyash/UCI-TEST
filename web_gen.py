import os
import json
import zipfile
import argparse
from textwrap import dedent
import google.generativeai as genai
from jinja2 import Template

# -----------------------------
# Config - put your Gemini key here for quick demo (NOT recommended for production)
# -----------------------------
GEMINI_API_KEY = "AIzaSyBpNKwiY-gIPGzIVZRZPbpuQ0Xou210028"  # <-- Replace with your key, or set via env and read below
# Example to use env var instead:
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# -----------------------------
# Templates (simple, embed here for demo)
# -----------------------------
INDEX_HTML_TEMPLATE = Template(dedent("""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ site_title }}</title>
  <meta name="description" content="{{ meta_description }}">
  <meta name="keywords" content="{{ meta_keywords }}">
  <!-- Open Graph -->
  <meta property="og:title" content="{{ site_title }}">
  <meta property="og:description" content="{{ meta_description }}">
  <meta property="og:type" content="website">
  <meta property="og:image" content="assets/og-image.png">
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{{ site_title }}">
  <meta name="twitter:description" content="{{ meta_description }}">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <h1>{{ site_title }}</h1>
    <p class="tagline">{{ tagline }}</p>
    <nav>
      <ul>
        {% for s in sections %}
        <li><a href="#{{ s.anchor }}">{{ s.title }}</a></li>
        {% endfor %}
      </ul>
    </nav>
  </header>

  <main>
    {% for s in sections %}
    <section id="{{ s.anchor }}" class="section">
      <h2>{{ s.title }}</h2>
      <p>{{ s.content }}</p>
    </section>
    {% endfor %}
  </main>

  <footer>
    <p>&copy; {{ year }} {{ site_title }} — Built with AI-powered scaffold</p>
  </footer>
  <script src="script.js"></script>
</body>
</html>
"""))

STYLES_CSS_TEMPLATE = Template(dedent("""
:root {
  --primary: {{ colors[0] }};
  --accent: {{ colors[1] if colors|length > 1 else '#ffffff' }};
  --bg: {{ colors[2] if colors|length > 2 else '#f8f8f8' }};
  --font-family: '{{ fonts[0] if fonts else "Inter, system-ui, sans-serif" }}', sans-serif;
}
* { box-sizing: border-box; }
body {
  font-family: var(--font-family);
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: #222;
}
.site-header {
  background: var(--primary);
  color: #fff;
  padding: 2rem;
  text-align: center;
}
.site-header nav ul { list-style: none; padding: 0; margin: 1rem 0 0 0; display:flex; gap:1rem; justify-content:center; }
.section { padding: 2rem; max-width: 900px; margin: 0 auto; }
footer { padding: 1rem; text-align: center; font-size: 0.9rem; background: #111; color: #fff; margin-top: 3rem; }
a { color: var(--accent); text-decoration: none; }
"""))

SCRIPT_JS_TEMPLATE = Template(dedent("""
document.addEventListener('DOMContentLoaded', function(){
  // Simple smooth scroll for navigation links
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function(e){
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    });
  });
});
"""))

# -----------------------------
# Helper functions
# -----------------------------
def call_gemini_generate(idea):
    """
    Calls Gemini model to produce a JSON describing the website scaffold.
    We instruct the model to output ONLY JSON in a fixed shape.
    """
    prompt = dedent(f"""
    You are a helpful website scaffold generator. The user will give a one-line business idea.
    Produce a JSON object only (no extra text) with the following keys:
    - site_title: short site title
    - tagline: short tagline
    - meta_description: 1-2 sentence description
    - meta_keywords: comma-separated keywords
    - colors: array of 2-4 hex colors (primary, accent, background, optional)
    - fonts: array with 1-2 font family names (for CSS)
    - sections: array of objects with keys: title, content, anchor
      Provide 3-5 sections suitable for the business idea.
    Example output:
    {{
      "site_title": "EcoWear",
      "tagline": "Sustainable fashion for everyone",
      "meta_description": "EcoWear sells sustainable clothing...",
      "meta_keywords": "sustainable, clothing, eco fashion",
      "colors": ["#2e8b57", "#ffffff", "#f6f6f6"],
      "fonts": ["Poppins", "Roboto"],
      "sections": [
        {{ "title": "Home", "content": "Welcome...", "anchor": "home" }},
        ...
      ]
    }}
    Now produce the JSON for this business idea: "{idea}"
    Make sure the JSON is parseable.
    """).strip()

    model = genai.GenerativeModel("models/gemini-2.5-pro")
    # Use generate_content or .responses depending on your SDK version; adjust if necessary.
    response = model.generate_content(prompt)
    text = response.text if hasattr(response, "text") else str(response)
    return text

def safe_parse_json(text):
    """
    Try to find JSON substring and parse. Common LLMs sometimes include backticks or stray text.
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to heuristically extract first { ... } block
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
    return None

def slugify(name):
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")

# -----------------------------
# Main flow
# -----------------------------
def generate_scaffold(business_idea, output_dir=None):
    print("🚀 Generating scaffold for idea:", business_idea)
    gemini_text = call_gemini_generate(business_idea)
    parsed = safe_parse_json(gemini_text)
    if parsed is None:
        print("❗ Failed to parse JSON from Gemini. Here's the raw response:")
        print(gemini_text)
        raise RuntimeError("Could not parse Gemini JSON output.")

    # Fill defaults where necessary
    site_title = parsed.get("site_title", business_idea.title())
    tagline = parsed.get("tagline", "")
    meta_description = parsed.get("meta_description", site_title + " - created from business idea")
    meta_keywords = parsed.get("meta_keywords", "")
    colors = parsed.get("colors", ["#2B7A78", "#FFFFFF", "#F8F8F8"])
    fonts = parsed.get("fonts", ["Inter"])
    sections = parsed.get("sections", [
        {"title": "Home", "content": "Welcome.", "anchor": "home"},
        {"title": "About", "content": "About us.", "anchor": "about"},
        {"title": "Contact", "content": "Contact us.", "anchor": "contact"},
    ])

    # Prepare output folder
    folder_name = output_dir or slugify(site_title) or "site_scaffold"
    os.makedirs(folder_name, exist_ok=True)
    assets_dir = os.path.join(folder_name, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # Render templates
    index_html = INDEX_HTML_TEMPLATE.render(
        site_title=site_title,
        tagline=tagline,
        meta_description=meta_description,
        meta_keywords=meta_keywords,
        colors=colors,
        fonts=fonts,
        sections=sections,
        year=2025
    )
    styles_css = STYLES_CSS_TEMPLATE.render(colors=colors, fonts=fonts)
    script_js = SCRIPT_JS_TEMPLATE.render()

    # Save files
    with open(os.path.join(folder_name, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    with open(os.path.join(folder_name, "styles.css"), "w", encoding="utf-8") as f:
        f.write(styles_css)
    with open(os.path.join(folder_name, "script.js"), "w", encoding="utf-8") as f:
        f.write(script_js)

    # Save a simple placeholder OG image file (empty PNG) so social meta points to something
    og_path = os.path.join(assets_dir, "og-image.png")
    with open(og_path, "wb") as f:
        f.write(b"")  # empty placeholder, replace with real image generation if needed

    # Create a zip archive of the scaffold
    zip_name = f"{folder_name}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_name):
            for file in files:
                full = os.path.join(root, file)
                arcname = os.path.relpath(full, start=folder_name)
                zf.write(full, arcname=os.path.join(folder_name, arcname))

    print("✅ Scaffold generated in folder:", folder_name)
    print("✅ Zip created:", zip_name)
    return folder_name, zip_name

# -----------------------------
# CLI entrypoint
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Website POC Generator (Gemini)")
    parser.add_argument("--idea", "-i", type=str, help="One-line business idea", required=True)
    parser.add_argument("--out", "-o", type=str, help="Output folder name (optional)", default=None)
    args = parser.parse_args()

    generate_scaffold(args.idea, args.out)
