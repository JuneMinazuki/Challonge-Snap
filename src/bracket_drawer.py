import aiohttp
import asyncio
from dotenv import load_dotenv
import os

# Load the api key from the .env file
load_dotenv()
CHALLONGE_API_KEY = os.getenv('CHALLONGE_API_KEY')

async def fetchChallongeSvg(bracket: str):
    url = f"https://challonge.com/{bracket}.svg"
    filename = "bracket.svg"
    
    # Headers are crucial to avoid 403 Forbidden errors from Challonge
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

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
                    # Write to file (standard file I/O blocks slightly, but is fine for small files)
                    with open(filename, "wb") as f:
                        f.write(content)
                    print(f"[asyncio] Success! Saved file as '{filename}'")
                else:
                    print("[Warning] The status was 200 OK, but the content does not look like an SVG.")
                    print(f"Content-Type: {content_type}")

        except aiohttp.ClientResponseError as e:
            print(f"[HTTP Error] {e.status} - {e.message}")
        except aiohttp.ClientError as e:
            print(f"[Connection Error] {e}")

async def fetchLastUpdate(session: aiohttp.ClientSession, tournamentID: str) -> tuple[str | None, bool]:
    url = f"https://api.challonge.com/v1/tournaments/{tournamentID}.json"
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
    async with aiohttp.ClientSession() as session:
        bracketId = input("Enter Bracket ID: ").strip()
        lastUpdate = await fetchLastUpdate(session, bracketId)

        if lastUpdate:
            print(f"Last Updated: {lastUpdate}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")