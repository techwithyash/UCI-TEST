import google.generativeai as genai

# 1. Set your API key directly here (⚠ Not safe for production!)
GEMINI_API_KEY = "AIzaSyAa9vdO4lUtxF8sR1CLaER9JnridG-zrYc"

# 2. Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# 3. Your blog article text
blog_text = """
Your blog article content goes here.. hi there this is a test
This is a sample blog article that will be used to generate social media content.
It contains multiple sentences and ideas that can be summarized or transformed into different formats.
Make sure to include enough context for the AI to understand the topic and tone.    
"""

# 4. Platform-specific prompts
prompts = {
    "twitter": f"Summarize the following article in 280 characters, witty tone, add 2 relevant hashtags:\n\n{blog_text}",
    "linkedin": f"Write a professional, engaging LinkedIn post (2-3 sentences) based on this article:\n\n{blog_text}",
    "instagram": f"Write a catchy Instagram caption based on this article, add 3 trending hashtags:\n\n{blog_text}",
    "facebook": f"Write a friendly, engaging Facebook post (3-4 sentences) encouraging comments based on:\n\n{blog_text}",
    "tiktok": f"Write a 10-second TikTok video script idea inspired by this article:\n\n{blog_text}"
}

# 5. Initialize Gemini model
model = genai.GenerativeModel("models/gemini-2.5-pro")

# 6. Generate content
outputs = {}
for platform, prompt in prompts.items():
    response = model.generate_content(prompt)
    # Debug: print the raw response
    print(f"\nRaw response for {platform}:", response)
    # Try to get text safely from different places
    text = None
    try:
        if hasattr(response, "text") and response.text:
            text = response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            # Try to extract from candidates
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                part = candidate.content.parts[0]
                if hasattr(part, "text"):
                    text = part.text.strip()
        if not text:
            text = "[No content returned]"
    except Exception as e:
        text = f"[No content returned: {e}]"
    outputs[platform] = text

# 7. Print results
for platform, text in outputs.items():
    print(f"\n--- {platform.upper()} ---\n{text}")
