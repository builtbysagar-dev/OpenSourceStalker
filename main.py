import discord
from discord.ext import commands, tasks
import aiohttp
import os
import random
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot Configuration
intents = discord.Intents.default()
intents.message_content = True

class OpenSourceStalker(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents, help_command=commands.DefaultHelpCommand())
        self.session = None
        # Structure: [{'repo': 'owner/repo', 'channel_id': 123, 'last_id': 123}]
        self.monitored_repos = []

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        self.check_repos.start()
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

    @tasks.loop(minutes=10)
    async def check_repos(self):
        """Background task to check for new issues in monitored repos."""
        if not self.monitored_repos:
            return

        print(f"Checking {len(self.monitored_repos)} repos...")
        
        for entry in self.monitored_repos:
            repo = entry['repo']
            channel_id = entry['channel_id']
            last_id = entry['last_id']
            
            url = f"https://api.github.com/repos/{repo}/issues"
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data:
                            continue
                            
                        latest_issue = data[0]
                        current_id = latest_issue['id']
                        
                        # If first time checking, just update the ID
                        if last_id is None:
                            entry['last_id'] = current_id
                            continue
                            
                        # If new issue found
                        if current_id != last_id:
                            channel = self.get_channel(channel_id)
                            if channel:
                                embed = discord.Embed(
                                    title="🚨 New Issue Alert!",
                                    description=f"A new issue has been opened in [{repo}]({latest_issue['html_url']})",
                                    color=discord.Color.red()
                                )
                                embed.add_field(name="Title", value=latest_issue['title'], inline=False)
                                embed.set_footer(text="OpenSourceStalker • Happy Coding!")
                                await channel.send(embed=embed)
                            
                            entry['last_id'] = current_id
                    elif response.status == 403:
                        print(f"Rate limited checking {repo}")
                    else:
                        print(f"Error checking {repo}: {response.status}")
            except Exception as e:
                print(f"Exception checking {repo}: {e}")

    @check_repos.before_loop
    async def before_check_repos(self):
        await self.wait_until_ready()

bot = OpenSourceStalker()

@bot.command(name='findissue', help='Finds a "good first issue" for a given language. Usage: !findissue <language>')
async def find_issue(ctx, language: str = 'python'):
    """
    Searches GitHub for issues with label 'good first issue' in the specified language.
    Default language is Python.
    """
    if not bot.session:
        bot.session = aiohttp.ClientSession()

    query = f'label:"good first issue" language:{language} state:open'
    params = {
        'q': query,
        'sort': 'updated',
        'order': 'desc'
    }
    url = "https://api.github.com/search/issues"

    try:
        async with bot.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                items = data.get('items', [])
                
                if not items:
                    await ctx.send(f"No 'good first issue' found for {language}. Try another language!")
                    return

                # Pick a random issue from top 30 (or fewer if less than 30)
                limit = min(len(items), 30)
                issue = random.choice(items[:limit])
                
                # Build Embed
                embed = discord.Embed(
                    title=issue['title'],
                    url=issue['html_url'],
                    color=discord.Color.green()
                )
                repo_name = issue['repository_url'].split('repos/')[-1]
                embed.add_field(name="Repository", value=repo_name, inline=True)
                embed.add_field(name="Comments", value=issue['comments'], inline=True)
                embed.set_footer(text=f"Found via OpenSourceStalker • Language: {language}")
                
                await ctx.send(embed=embed)
            
            elif response.status == 403:
                await ctx.send("Rate limit exceeded. Please try again later.")
            else:
                await ctx.send(f"Error fetching issues: {response.status}")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command(name='stalk', help='Monitors a repository for new issues. Usage: !stalk <owner>/<repo>')
async def stalk_repo(ctx, repo_name: str):
    """
    Adds a repository to the watch list. 
    The bot will check for new issues every 10 minutes and notify in this channel.
    Example: !stalk facebook/react
    """
    if '/' not in repo_name:
        await ctx.send("Invalid format. Please use `owner/repo` (e.g., `facebook/react`).")
        return

    # Check if already monitoring in this channel
    for entry in bot.monitored_repos:
        if entry['repo'] == repo_name and entry['channel_id'] == ctx.channel.id:
            await ctx.send(f"Already stalking {repo_name} in this channel!")
            return

    # Add to monitored list
    # We initialize last_id as None, it will be populated on next loop run
    bot.monitored_repos.append({
        'repo': repo_name,
        'channel_id': ctx.channel.id,
        'last_id': None
    })
    
    await ctx.send(f"👀 Now stalking **{repo_name}**. I'll let you know if a new issue pops up!")

if __name__ == '__main__':
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file.")
    else:
        keep_alive()
bot.run(TOKEN)
