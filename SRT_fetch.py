import requests
import re
import sys
import json

# ==========================================
# CONFIGURATION - SANDBOX CREDENTIALS
# ==========================================
SERVER = "{SERVER}"
CLIENT_ID = "{ID}"
CLIENT_SECRET = "{SECRET}"
USERNAME = "{USERNAME}"
PASSWORD = "{PASSWORD}"
SESSION_ID = "{SESSION_ID}"
# ==========================================

def get_clean_text_from_srt(srt_content):
    """Strips timestamps, sequence numbers, HTML tags, and bracketed notes to leave clean text."""
    
    # 1. Remove the timestamp line completely (e.g., "00:00:03,240 --> 00:00:06,720")
    text = re.sub(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', '', srt_content)
    
    # 2. Remove standalone sequence numbers (lines with only numbers on them)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # 3. Remove bracketed metadata like [Auto-generated transcript...] or [Music]
    text = re.sub(r'\[.*?\]', '', text)
    
    # 4. Remove any rogue HTML tags (like <span> or <br>)
    text = re.sub(r'<[^>]+>', '', text)
    
    # 5. Clean up extra whitespace and newlines by splitting and re-joining
    words = text.split()
    return ' '.join(words)

def main():
    print(f"Starting transcript extraction for Session: {SESSION_ID}")
    
    session = requests.Session()
    
    # ---------------------------------------------------------
    # STEP 1: Get standard OAuth2 Token
    # ---------------------------------------------------------
    print("1. Authenticating with Panopto OAuth2...")
    token_url = f"https://{SERVER}/Panopto/oauth2/connect/token"
    
    token_payload = {
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD,
        'scope': 'api'
    }
    
    # Panopto expects the Client ID and Secret as Basic Auth in the headers.
    token_res = session.post(
        token_url, 
        auth=(CLIENT_ID, CLIENT_SECRET), 
        data=token_payload
    )
    
    if token_res.status_code != 200:
        print(f"Error getting token: HTTP {token_res.status_code}")
        sys.exit(1)
        
    access_token = token_res.json().get('access_token')
    
    # ---------------------------------------------------------
    # STEP 2: Exchange Token for .ASPXAUTH Cookie
    # ---------------------------------------------------------
    print("2. Exchanging OAuth Token for Legacy Session Cookie...")
    legacy_login_url = f"https://{SERVER}/Panopto/api/v1/auth/legacyLogin"
    
    headers = {'Authorization': f'Bearer {access_token}'}
    session.get(legacy_login_url, headers=headers)
    
    if '.ASPXAUTH' not in session.cookies.get_dict():
        print("Failed to obtain .ASPXAUTH cookie.")
        sys.exit(1)

    # ---------------------------------------------------------
    # STEP 3: Download the SRT File 
    # ---------------------------------------------------------
    print("3. Fetching SRT...")
    srt_url = f"https://{SERVER}/Panopto/Pages/Transcription/GenerateSRT.ashx"
    
    languages_to_try = ['1', '0', '2', 'English_UK', 'English_USA']
    
    srt_text = ""
    found_language = None
    
    for lang in languages_to_try:
        srt_params = {'id': SESSION_ID, 'language': lang}
        srt_res = session.get(srt_url, params=srt_params)
        
        if srt_res.status_code == 200 and srt_res.text.strip():
            srt_text = srt_res.text
            found_language = lang
            break
            
    if not srt_text:
        print("Failed to find captions.")
        sys.exit(1)
        
    print(f"   -> Success! Found captions using language ID: {found_language}")
        
    # ---------------------------------------------------------
    # STEP 4: Clean and Save as JSON
    # ---------------------------------------------------------
    print("4. Cleaning and formatting as JSON...")
    clean_text = get_clean_text_from_srt(srt_text)
    
    chatbot_payload = {
        "source": "Panopto",
        "session_id": SESSION_ID,
        "language_track": found_language,
        "transcript": clean_text
    }
    
    output_filename = f"transcript_{SESSION_ID}.json"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(chatbot_payload, f, indent=4)
        
    print(f"Done! JSON saved to {output_filename}")

if __name__ == "__main__":
    main()
