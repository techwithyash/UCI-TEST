import google.generativeai as genai

# Your API key
API_KEY = "AIzaSyCNa9iyOeWzZXUeKyADPrdZGMWw6PRFxaQ"  # Replace with your actual Gemini API key
genai.configure(api_key=API_KEY)

# Read HTML file from current directory
with open("input.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# Prompt for SEO optimization
prompt = f"""
You are an SEO expert. Improve the SEO of the following HTML:
1. Add a descriptive <title> if missing.
2. Add/improve meta description & keywords.
3. Add alt text to all <img> tags.
4. Add Open Graph & Twitter Card tags.
5. Preserve existing styles and scripts.

HTML:
{html_content}
"""

# Call Gemini API
model = genai.GenerativeModel("models/gemini-2.5-pro")
response = model.generate_content(prompt)

# Save optimized HTML into .html file
optimized_html = response.text
with open("optimized_output.html", "w", encoding="utf-8") as f:
    f.write(optimized_html)

print("✅ SEO optimized HTML saved as optimized_output.html")
