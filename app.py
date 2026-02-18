import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# This grabs the key from the secure Streamlit settings
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Missing API Key. Go to Streamlit Settings -> Secrets.")

# THE EXACT MODEL YOU REQUESTED
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    generation_config={"temperature": 0.0}
)

# --- SYSTEM PROMPT ---
SYSTEM_INSTRUCTION = """
# ROLE
You are a ruthless Senior EU Compliance Officer. Audit the text against the EU Green Claims Directive (2026).

# LEGAL RULES (THE CONSTRAINTS)
1. BANNED GENERIC TERMS: "Eco-friendly", "Green", "Sustainable", "Ecological", "Climate friendly", "Biodegradable" are ILLEGAL without ISO Type I certification.
2. CARBON NEUTRALITY: Claims of "Carbon Neutral" or "CO2 Compensated" are ILLEGAL if based on offsets.
3. FUTURE CLAIMS: "Net Zero" or "2030/2040 goals" are ILLEGAL without a publicly available, verified 2030 implementation roadmap.
4. COMPARISONS: "Less plastic" or "Greenest" are ILLEGAL without a specific baseline.

# SCORING MATH (STRICT DETERMINISTIC LOGIC)
- Base Score: 0%
- +20% for each unique Banned Generic Term found (capped at 60%).
- +30% if a Net Zero/Carbon Neutral claim exists without a 2030 Roadmap.
- +10% for each comparative claim lacking a specific baseline.
- MAX SCORE: 100%.

# OUTPUT FORMAT
- RISK SCORE: [Calculation result]%
- ESTIMATED FINE: [Calculated as: Risk Score / 25]% of Global Annual Turnover
- VIOLATIONS: 
  * **[Term]** | [Legal Reason] | [Compliant Rewrite]
- SUMMARY: 2 sentences on the legal jeopardy and immediate action required.
"""

# --- SCRAPING FUNCTION (MANUAL MODE) ---
def scrape_website(url):
    # Spoof a real browser to bypass basic anti-bot protection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return f"Error: Website blocked the scraper (Status Code: {response.status_code})"
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Kill script and style elements (removes noise)
        for script in soup(["script", "style"]):
            script.extract()

        text = ' '.join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'li'])])
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text[:50000] 
    except Exception as e:
        return f"Error scraping website: {e}"

# --- THE WEBSITE UI CONFIGURATION ---
st.set_page_config(page_title="ZeroWash.ai", page_icon="🛡️")

# --- GLOBAL STYLES (Hide Anchors, Hide Branding, Enterprise Theme) ---
st.markdown("""
    <style>
    /* 1. HIDE ANCHOR LINKS (The Chain Icon) - Nuclear Option */
    [data-testid="stHeaderAction"] { display: none !important; }
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; pointer-events: none; cursor: default; }
    .st-emotion-cache-1wbqy5l { display: none !important; }

    /* 2. HIDE STREAMLIT BRANDING */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* 3. ENTERPRISE THEME */
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Arial', sans-serif;
    }

    /* 4. PROFESSIONAL BUTTON STYLE */
    .stButton>button {
        background-color: #0056b3; /* Corporate Blue */
        color: white;
        border: none;
        border-radius: 4px;
        padding: 12px 24px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #004494;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* 5. WARNING BOX STYLE */
    div[data-testid="stMarkdownContainer"] > h3 {
        color: #d32f2f; /* Compliance Red */
        padding-bottom: 10px;
        border-bottom: 2px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)
st.title("🛡️ ZeroWash.ai")
st.subheader("Automated Compliance for the 2026 Green Claims Directive")
st.info("Paste the EXACT link to the sustainability page.")


url_input = st.text_input("Target URL (e.g., https://www.hm.com/sustainability)", "")

if st.button("Audit Website"):
    if not url_input:
        st.warning("Please enter a URL.")
    else:
        with st.spinner("🕵️‍♂️ Extracting legal text..."):
            website_text = scrape_website(url_input)
            
            if "Error" in website_text:
                st.error(website_text)
            else:
                st.success(f"✅ Text Extracted. Length: {len(website_text)} chars")
                with st.spinner("⚖️ Cross-referencing EU Laws..."):
                    prompt = f"{SYSTEM_INSTRUCTION}\n\nANALYZE THIS CONTENT:\n{website_text}"
                    try:
                        response = model.generate_content(prompt)
                        st.markdown("### 🚨 Compliance Report")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"API Error: {e}")