<div align="center">
  
  <img width="650" alt="Banner" src="https://github.com/user-attachments/assets/1a93e3a5-a99e-47c7-b156-d4c915fc7663" />
  
  [![Release version](https://img.shields.io/github/v/release/JuneMinazuki/Challonge-Snap?color=brightgreen&label=Setup%20and%20Deployment&style=for-the-badge)](#setup-and-deployment "Setup & Deployment")

</div>

<p align="center">
  A Discord bot that fetches Challonge's tournament brackets, renders and posts them into a channel.
  <br>
  <b>Note:</b> This is a self-hosted bot. You will need to create your own Discord Application and run the code on your own machine/server.
  <br>
  <br>
  <a href="#features">Features</a> •
  <a href="#commands">Commands</a> •
  <a href="#requirements">Requirements</a> •
  <a href="#permissions">Permissions</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

<h2 id="features">✨ Features</h2>

1. **Real-time Rendering:** Converts live Challonge data into a clean image format.
2. **Auto-Update:** Automatically refreshes the bracket image in Discord when scores are reported. **Note:** Auto-update function only work with a Challonge API given.
3. **Tournament Support:** Works with Single Elim, Double Elim, Swiss Stage and Round Robin formats.
4. **Simple Commands:** Minimalistic setup for tournament organizers.

<h2 id="commands">⌨️ Commands</h2>

The bot uses **Slash Commands**. Ensure the bot has `Use Application Commands` permission in your server.

| Command    | Usage                      | Description                                                   |
| :---       | :---                       | :---                                                          |
| `/bracket` | `/bracket <tournament_id>` | Fetches the Challonge bracket and posts the rendered bracket. |
| `/info`    | `/info`                    | Get current active tournament ID.                             |
| `/update`  | `/update`                  | Forces an immediate refresh of the currently active bracket.  |

<h2 id="requirements">📋 Requirements</h2>

1. **Discord Bot Token:** Create one via the [Discord Developer Portal](https://discord.com/developers/applications)
2. **Environment:** Python 3.14+

**Optional:**
1. **Challonge API Key:** Obtainable from your [Challonge Settings](https://challonge.com/settings/developer) (Required for auto-update feature)

<h2 id="permissions">🛡️ Permissions</h2>

To function correctly with all features, the bot requires the following permissions as configured in the Discord Developer Portal:

- View Channels
- Send Messages
- Send Messages in Threads
- Manage Messages
- Attach Files
- Read Message History

<h2 id="contributing">🤝 Contributing</h2>
Contributions are what make the open-source community such an amazing place to learn, inspire, and create.

1. **Fork** the Project.
2. Create your **Feature Branch** (`git checkout -b feature/AmazingFeature`).
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`).
4. **Push** to the branch (`git push origin feature/AmazingFeature`).
5. Open a **Pull Request**.

<h2 id="license">📄 License</h2>

Distributed under the **MIT License**. See `LICENSE` for more information.
