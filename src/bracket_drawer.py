import asyncio
import os
import re
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp
import cairosvg
from dotenv import load_dotenv

from json_handler import load_json, save_json

# Load the api key from the .env file
load_dotenv()
CHALLONGE_API_KEY: str | None = os.getenv('CHALLONGE_API_KEY')

# Get last_update
user_data: dict[str, Any] = load_json()
last_update: str | None = user_data.get("last_update")

# Headers are crucial to avoid 403 Forbidden errors from Challonge
HEADERS: dict[str, str] = {
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

async def get_tournament_id(session: aiohttp.ClientSession, tournament_id: str) -> str | None:
    """Extracts the internal numeric ID from the public Challonge page."""
    url: str = f"https://challonge.com/{tournament_id}"
    print(f"[aiohttp] Looking up ID from public page: {url}")

    async with session.get("https://challonge.com/") as resp:
        await resp.text()

    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"[Error] Failed to load page. Status: {response.status}")
                return None

            # Get HTML content
            html: str = await response.text()
            
            # Find the ID hidden in the JavaScript
            match = re.search(r'"tournament":\s*\{\s*"id":\s*(\d+)', html)
            
            if match:
                found_id: str = match.group(1)
                print(f"[aiohttp] Found Tournament ID: {found_id}")
                return found_id
            else:
                print("[Error] Could not find tournament ID in page source.")
                return None

    except Exception as e:
        print(f"[Error] Error looking up ID: {e}")
        return None
    
async def fetch_challonge_bracket(session: aiohttp.ClientSession, tournament_id: str) -> bytes | None:
    """Draw the challonge bracket"""
    url: str = f"https://challonge.com/{tournament_id}.svg"

    async with session.get("https://challonge.com/") as resp:
        await resp.text()

    print(f"[aiohttp] Attempting to fetch: {url}")

    try:
        async with session.get(url) as response:
            # Raise an exception for 4xx/5xx status codes
            response.raise_for_status()
            
            # Check content type to ensure it's likely an SVG
            content_type: str = response.headers.get("Content-Type", "")
            
            # Read the binary content
            content: bytes = await response.read()

            # Basic validation (check for SVG/XML signature)
            if "image/svg+xml" in content_type or b"<svg" in content[:100].lower():
                edited_content: bytes = await edit_svg(content)

                print("[cairosvg] Converting SVG to bytes...")

                # Convert svg to bytes
                image_bytes: bytes | None = await asyncio.to_thread(
                    cairosvg.svg2png, 
                    bytestring=edited_content,
                    scale=2
                )
                
                print(f"[cairosvg] Image sucessfully convert to bytes")
                return image_bytes
            else:
                print("[Warning] The status was 200 OK, but the content does not look like an SVG.")
                print(f"Content-Type: {content_type}")
                return None

    except aiohttp.ClientResponseError as e:
        print(f"[HTTP Error] {e.status} - {e.message}")
        return None
    
    except aiohttp.ClientError as e:
        print(f"[Connection Error] {e}")
        return None

async def fetch_last_update(session: aiohttp.ClientSession, tournament_id: str) -> tuple[str | None, bool]:
    """Get last update time and status of tournament (completed or not)"""
    # Find the hidden tournament id
    hidden_id: str | None = await get_tournament_id(session, tournament_id)
    if not hidden_id:
            hidden_id = tournament_id
    
    url: str = f"https://api.challonge.com/v1/tournaments/{hidden_id}.json"
    PARAMS: dict[str, Any] = {
        "api_key": CHALLONGE_API_KEY,
        "include_matches": 0,
        "include_participants": 0
    }

    try:
        async with session.get(url, params=PARAMS) as response:
            response.raise_for_status()
            data: dict[str, Any] = await response.json()

            tournament: dict[str, Any] = data['tournament']
            last_update: str = tournament['updated_at']
            state: str = tournament['state']
            is_finished: bool = state in ("complete", "awaiting_review")

            return last_update, is_finished
            
    except Exception as e:
        print(f"[Error Fetching Data] {e}")
        return None, False

async def edit_svg(content: bytes, padding: int = 40) -> bytes:
    """Convert svg from website into bytes"""
    print("[xml] Editing SVG file")

    # Register namespaces to prevent 'ns0' prefixes in output
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree_root = ET.fromstring(content)

    HEADER_OFFSET = 110 # Challonge header
    MATCH_CARD_HEIGHT = 55 # Height of one bracket node
    MATCH_CARD_WIDTH = 220 # Width of one bracket node
    
    max_x: float = 0
    max_y: float = 0
    is_found: bool = False

    # Regex to pull coordinates from strings
    translate_pattern = re.compile(r"translate\(\s*([\d.]+)[ ,]+([\d.]+)\s*\)")

    for elem in tree_root.iter():
        transform = elem.get('transform')
        if transform:
            match = translate_pattern.search(transform)
            if match:
                x = float(match.group(1))
                y = float(match.group(2))
                
                if x > max_x: max_x = x
                if y > max_y: max_y = y
                is_found = True

    # Calculate new dimensions based on findings
    if is_found:
        # Content Height = Header + Lowest Match Y + Match Height
        content_height: float = HEADER_OFFSET + max_y + MATCH_CARD_HEIGHT
        
        # Content Width = Furthest Match X + Match Width
        content_width: float = max_x + MATCH_CARD_WIDTH
    else:
        # Fallback if parsing fails
        content_width = float(tree_root.get('width', 800))
        content_height = float(tree_root.get('height', 600))

    # Add padding
    final_width: float = content_width + (padding * 2)
    final_height: float = content_height + (padding * 1.5)

    # Update root attributes
    tree_root.set('width', str(final_width))
    tree_root.set('height', str(final_height))
    tree_root.set('viewBox', f"-{padding} -{padding} {final_width} {final_height}")

    # Add white background
    bg_rect = ET.Element('rect', {
        'x': f"-{padding}",
        'y': f"-{padding}",
        'width': str(final_width),
        'height': str(final_height),
        'fill': 'white'
    })
    
    # Insert at index 0 ensures it is in background
    tree_root.insert(0, bg_rect)

    return ET.tostring(tree_root)

async def get_latest_bracket(tournament_id: str) -> tuple[bytes | None, bool]:
    """Check for update, then update the bracket only when necessary"""
    global last_update
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        update_time, is_complete = await fetch_last_update(session, tournament_id)

        if (last_update == update_time):
            print("[bracket_drawer] No update needed.")
            return None, is_complete
        
        print(f"[bracket_drawer] Update found for {tournament_id}.")
        
        # Update last_update
        last_update = update_time
        user_data["last_update"] = update_time
        save_json(user_data)

        return await fetch_challonge_bracket(session, tournament_id), is_complete

async def main():
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        bracket_id = input("Enter Bracket ID: ").strip()
        await fetch_challonge_bracket(session, bracket_id)
        update_time, is_complete = await fetch_last_update(session, bracket_id)

        if last_update:
            print(f"Last Updated: {update_time}")
            print(f"Completed: {is_complete}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")