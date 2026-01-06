import aiohttp
import asyncio
import cairosvg
from dotenv import load_dotenv
import os
import re

# Load the api key from the .env file
load_dotenv()
CHALLONGE_API_KEY = os.getenv('CHALLONGE_API_KEY')

# Headers are crucial to avoid 403 Forbidden errors from Challonge
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://challonge.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Connection": "keep-alive"
}

async def getTournamentID(session: aiohttp.ClientSession, tournamentID: str):
    url = f"https://challonge.com/{tournamentID}"
    print(f"[aiohttp] Looking up ID from public page: {url}")

    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"[Error] Failed to load page. Status: {response.status}")
                return None
            
            # Get HTML content
            html = await response.text()
            
            # Find the ID hidden in the JavaScript
            match = re.search(r'"tournament":\s*\{\s*"id":\s*(\d+)', html)
            
            if match:
                found_id = match.group(1)
                print(f"[aiohttp] Found Tournament ID: {found_id}")
                return found_id
            else:
                print("[Error] Could not find tournament ID in page source.")
                return None

    except Exception as e:
        print(f"[Error] Error looking up ID: {e}")
        return None
    
async def fetchChallongeSvg(bracket: str):
    url = f"https://challonge.com/{bracket}.svg"
    filename = "bracket.png"

    print(f"[aiohttp] Attempting to fetch: {url}")

    # Create an async session
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                # Raise an exception for 4xx/5xx status codes
                response.raise_for_status()
                
                # Check content type to ensure it's likely an SVG
                content_type = response.headers.get("Content-Type", "")
                
                # Read the binary content
                content = await response.read()

                # Basic validation (check for SVG/XML signature)
                if "image/svg+xml" in content_type or b"<svg" in content[:100].lower():
                    print("[cairosvg] Converting SVG to PNG...")

                    # Convert svg to png
                    await asyncio.to_thread(
                        cairosvg.svg2png, 
                        bytestring = content, 
                        write_to = filename
                    )
                    
                    print(f"[Success] Saved file as '{filename}'")
                else:
                    print("[Warning] The status was 200 OK, but the content does not look like an SVG.")
                    print(f"Content-Type: {content_type}")

        except aiohttp.ClientResponseError as e:
            print(f"[HTTP Error] {e.status} - {e.message}")
        except aiohttp.ClientError as e:
            print(f"[Connection Error] {e}")

async def fetchLastUpdate(session: aiohttp.ClientSession, tournamentID: str) -> tuple[str | None, bool]:
    # Find the hidden tournament id
    hiddenID = await getTournamentID(session, tournamentID)
    if not hiddenID:
            hiddenID = tournamentID
    
    url = f"https://api.challonge.com/v1/tournaments/{hiddenID}.json"
    params = {
        "api_key": CHALLONGE_API_KEY,
        "include_matches": 0,
        "include_participants": 0
    }

    try:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()

            tournament = data['tournament']
            lastUpdate = tournament['updated_at']
            state = tournament['state']
            isFinished = (state == "complete") or (state == "awaiting_review")

            return lastUpdate, isFinished
            
    except Exception as e:
        print(f"[Error Fetching Data] {e}")
        return None, False

async def main():
    async with aiohttp.ClientSession(headers=headers) as session:
        bracketId = input("Enter Bracket ID: ").strip()
        await fetchChallongeSvg(bracketId)
        lastUpdate = await fetchLastUpdate(session, bracketId)

        if lastUpdate:
            print(f"Last Updated: {lastUpdate}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")