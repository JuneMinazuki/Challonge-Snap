# Contributing to Challonge-Snap

First off, thank you for considering contributing! It’s people like you who make this bot a great tool for the tournament community.

## 🚀 How Can I Contribute?

### Reporting Bugs

- Check the [Issues](https://github.com/JuneMinazuki/Challonge-Snap/issues) to see if the bug has already been reported.

- If not, open a new issue. Include steps to reproduce, your Python version, and any relevant error logs (scrub your API keys first!).

### Suggesting Enhancements

- We welcome ideas for new rendering styles (e.g., different bracket themes) or Discord features.

- Open an issue and describe the "why" and "how" of your suggestion.

### Local Environment Setup

1. **Fork** the repository and create your branch from `main`.

2. **Setup Project On Your Local Machine:**
```bash
# Clone your fork
git clone https://github.com/your-username/repo-name.git
cd repo-name

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dev dependencies
pip install -r requirements-dev.txt
```

3. **Setup Environment:** Create a `.env` file with your `DISCORD_TOKEN`.

## 📝 Contribution Guidelines

### Prerequisites

1. Python 3.14.2

2. CairoSVG

    * **MacOS:** Use `Homebrew` to install the required libraries.
    ```bash
    brew install cairo pango gdk-pixbuf libffi
    ```

    * **Linux:** Install the development headers and the shared libraries via `apt`.
    ```bash
    sudo apt-get update
    sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
    ```

    * **Windows:**
        1. Download the [lastest GTK3 Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases).

        2. Run the installer and keep note of the installation path (usually `C:\Program Files\GTK3-Runtime Win64`).

        3. Press `Win` key and search for `"Edit the system environment variables"`.

        4. Click `Environment Variables`.

        5. Under System variables (bottom box), find the variable named `Path` and click Edit.

        6. Click `New` and paste the path to the bin folder of your GTK installation (e.g. `C:\Program Files\GTK3-Runtime Win64\bin`).

        7. Click OK on all windows to save.

        8. Restart your terminal/VS Code and reopen it so the new PATH takes effect.

### Branching Strategy

- **Main Branch:** Stable code. Do not PR directly to main without an issue reference.

- **Feature Branches:** Use `tag/your-feature-name`.

### Commit Messages
We follow a simple convention for clarity:

- `[add]`: A new feature.

- `[improve]`: A new feature.

- `[fix]`: A bug fix.

- `[docs]`: Changes to documentation.

### Code Style

- Ensure your code follows [PEP 8](https://peps.python.org/pep-0008/) standards.

- Use **Type Hinting** for new functions (e.g., `async def get_bracket(id: str) -> io.BytesIO:`).

- Ensure `.env` variables are used for tokens. **Never** hardcode your API keys.

- **No Blocking Calls:** To keep the bot responsive, do not use `requests`, `time.sleep()`, or synchronous file I/O. Use `aiohttp` for all API calls and `aiofiles` for file operations.

### Testing

Before submitting a Pull Request, verify:

- The bot logs in and responds to commands.

- The `CairoSVG` conversion does not clip the edges of the bracket for both small (4-man) and large (64-man) brackets.

- The image displays correctly on mobile Discord clients.

- Images are optimized for Discord’s file size limits (8MB for non-Nitro).

- Ensure all `aiohttp` sessions are closed properly to prevent memory leaks.

## 🎨 Rendering Pipeline

1. **Command Trigger:** A user requests a bracket.

2. **Request:** `aiohttp` sends the request to Challonge.

3. **Yield:** The bot "yields" control back to the event loop, allowing it to respond to other messages.

4. **Render:** Once the SVG data arrives, `CairoSVG` converts SVGs to PNGs, and `Pillow` is used for final compositions.

5. **Post:** `dicord.py` sends the final PNG back to the channel.

## 🚀 How to Submit a Pull Request

1. Update the `README.md` if you changed how a command works.

2. Push your changes to your fork.

3. Open a Pull Request with a clear description of what was added or fixed.

## ⚖️ License
By contributing, you agree that your code will be licensed under the project's `MIT License`.