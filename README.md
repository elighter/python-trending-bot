# Python Trending Bot for Bluesky

A Twitter-like bot that shares trending Python GitHub repositories on Bluesky as a thread.

## 🚀 Features

- Automatically fetches trending Python repositories from GitHub
- Creates a well-formatted thread on Bluesky with repository details
- Customizable number of repositories to share
- Runs on schedule or on-demand
- Easy to set up and configure

## 📋 Requirements

- Python 3.10 or higher
- Bluesky account
- GitHub Personal Access Token (optional, helps with API rate limits)

## 🔧 Installation

1. Clone this repository:
```bash
git clone https://github.com/elighter/python-trending-bot.git
cd python-trending-bot
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your credentials:
```bash
cp .env.example .env
```

4. Edit the `.env` file with your information:
```
BLUESKY_USERNAME=yourusername.bsky.social
BLUESKY_PASSWORD=your-app-password
GITHUB_TOKEN=your-github-token
POST_COUNT=5
```

## 🏃‍♂️ Running the Bot

### Local Execution

To run the bot locally:

```bash
python bot.py
```

### Automated Execution with GitHub Actions

This repository includes a GitHub Actions workflow that automatically runs the bot on a schedule. To use it:

1. Add your Bluesky credentials and GitHub token as repository secrets in your GitHub repository:
   - `BLUESKY_USERNAME`: Your Bluesky username
   - `BLUESKY_PASSWORD`: Your Bluesky app password
   - `GH_PAT`: Your GitHub Personal Access Token

2. The workflow will run automatically according to the schedule defined in `.github/workflows/bot.yml` (default: every 6 hours).

## 📝 How It Works

1. The bot fetches trending Python repositories from GitHub
2. It formats the data into a series of posts
3. It creates a thread on Bluesky with:
   - An introductory post
   - Individual posts for each repository with details (stars, forks, description, URL)
   - A final post with hashtags

## 🛠️ Customization

You can customize various aspects of the bot:

- `POST_COUNT`: Number of repositories to share (default: 5)
- `POST_INTERVAL`: Time between posts in seconds (default: 3600)
- Schedule in the GitHub Actions workflow file

## 🚀 Future Improvements

Here are some planned features for future versions:

- Highlight fast-growing new projects alongside repository details
- Interactive features (responding to specific hashtags or questions)
- Filter Python projects by specific domains (AI, web development, data science)
- Weekly summaries of trending repositories
- Custom visualizations for repository statistics

Feel free to contribute to any of these features or suggest new ones!

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [atproto](https://github.com/MarshalX/atproto) - Python client for the AT Protocol
- GitHub API for providing trending repository data

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/elighter/python-trending-bot/issues).

---

Created by [@emrecakmak.me](https://bsky.app/profile/emrecakmak.me)
