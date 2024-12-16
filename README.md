# Bella Discord Bot

A versatile Discord bot powered by Google's Gemini AI, capable of natural conversations, image generation, and voice message processing.

## Features

- Natural conversation using Gemini AI
- Image generation capabilities
- Voice message processing
- Multi-language support (English & Arabic)
- Memory management system
- Web server status monitoring

## Prerequisites

- Python 3.11 or higher
- Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
- Google Gemini API Key (from [Google AI Studio](https://makersuite.google.com/app/apikey))
- FFmpeg (for voice processing)

## Setup

1. Clone the repository:
```

## Deployment on Railway

1. Fork this repository to your GitHub account

2. Create a new project on [Railway](https://railway.app/)

3. Click "Deploy from GitHub repo" and select your forked repository

4. Add Environment Variables in Railway Dashboard:
   - Go to your project settings
   - Click on "Variables"
   - Add the following variables:
     ```
     DISCORD_TOKEN=your_discord_token
     GEMINI_API_KEY=your_gemini_api_key
     ```

5. Railway will automatically deploy your bot

6. To update the bot:
   - Push changes to your GitHub repository
   - Railway will automatically redeploy

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| DISCORD_TOKEN | Your Discord bot token | Yes |
| GEMINI_API_KEY | Your Google Gemini API key | Yes |
| DEBUG | Enable debug mode (True/False) | No |
| BACKUP_INTERVAL | Memory backup interval in seconds | No |