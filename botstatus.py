import discord
from discord.ext import commands
import os
import datetime

# Channel IDs
CONTROLLER_CHANNEL_ID = 1400377520771174450
ANNOUNCEMENT_CHANNEL_ID = 1400372201290731540
LOG_CHANNEL_ID = 1400372313001693234  # Log channel

CONTROL_PANEL_MSGID_FILE = "control_panel_msgid.txt"

GIFS = {
    "online": "https://media.discordapp.net/attachments/1400375199949393940/1400375322435780669/online.gif?width=850&height=300",
    "restart": "https://media.discordapp.net/attachments/1400375199949393940/1400375328098095144/restart.gif?width=850&height=300",
    "dev_mode": "https://media.discordapp.net/attachments/1400375199949393940/1400375850544926761/DEV_MODE.gif?width=850&height=300",
    "custom_restart": "https://media.discordapp.net/attachments/1400375199949393940/1400375328098095144/restart.gif?width=850&height=300"
}

ANNOUNCEMENTS = {
    "online": "## ✅ **Bot Back Online** \n\n The bot is now back online and fully operational after a quick maintenance restart. Everything is running smoothly again — thank you for waiting!",
    "restart": "## ⚡  **Quick Restart Notice** \n\n The bot will be restarting shortly for a quick maintenance update to ensure everything runs smoothly. It will be back online in just a moment, so thank you for your patience and understanding!",
    "dev_mode": "## 🛠️ **Developer Mode ** \n\n The bot is now back online in developer mode after a quick restart. Some features may be under testing, so you might notice a few changes or temporary tweaks as we work on new updates.",
    "custom_restart": "## ⚡ **Restart Notice** \n The bot is restarting to apply updates and improvements. Some features may be temporarily unavailable during this process, but it will be back online shortly — thank you for your patience!"
}


async def log_action(bot, user: discord.User, action: str):
    """Send log entry to log channel."""
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await log_channel.send(f"📝 **Log:** `{user}` pressed **{action}** at `{timestamp}`")


class TimeModal(discord.ui.Modal):
    def __init__(self, bot, action_key: str, update_embed_callback):
        super().__init__(title=f"Enter Time for {action_key.replace('_', ' ').title()}")
        self.bot = bot
        self.action_key = action_key
        self.update_embed_callback = update_embed_callback

        self.time_input = discord.ui.TextInput(
            label="Time",
            placeholder="e.g., 10:30 AM",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        time_str = self.time_input.value.strip()
        announcement_channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if announcement_channel:
            embed = discord.Embed(
                description=f"{ANNOUNCEMENTS[self.action_key]}\n**Time:** {time_str}",
                color=discord.Color.blue() if self.action_key == "dev_mode" else discord.Color.red()
            )
            await announcement_channel.send(embed=embed)  # No title, no GIF

        await log_action(self.bot, interaction.user, f"{self.action_key} (Time: {time_str})")

        # Respond to the interaction first (important)
        await interaction.response.send_message(f"Announcement sent for {time_str}!", ephemeral=True)

        # Then update the control panel embed GIF
        await self.update_embed_callback(self.action_key)


class ControlPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Online", style=discord.ButtonStyle.success, custom_id="btn_online"))
        self.add_item(discord.ui.Button(label="Restart", style=discord.ButtonStyle.primary, custom_id="btn_restart"))
        self.add_item(discord.ui.Button(label="Dev Mode", style=discord.ButtonStyle.secondary, custom_id="btn_dev_mode"))
        self.add_item(discord.ui.Button(label="Custom Restart", style=discord.ButtonStyle.danger, custom_id="btn_custom_restart"))


class ControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.panel_message_id = None
        if os.path.exists(CONTROL_PANEL_MSGID_FILE):
            with open(CONTROL_PANEL_MSGID_FILE, "r") as f:
                try:
                    self.panel_message_id = int(f.read().strip())
                except ValueError:
                    self.panel_message_id = None

    async def update_control_panel_embed(self, action_key, interaction=None):
        """Update the control panel embed image."""
        channel = self.bot.get_channel(CONTROLLER_CHANNEL_ID)
        if not channel or not self.panel_message_id:
            return

        try:
            panel_msg = await channel.fetch_message(self.panel_message_id)
        except discord.NotFound:
            return

        embed = discord.Embed(
            title="Bot Control Panel",
            description="Use the buttons below to send announcements.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIFS[action_key])
        await panel_msg.edit(embed=embed, view=ControlPanelView())

        # If interaction is provided and not responded yet, respond now
        if interaction and not interaction.response.is_done():
            await interaction.response.send_message(f"✅ Panel updated to `{action_key}` state.", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        """Ensure control panel is sent when bot is ready."""
        channel = self.bot.get_channel(CONTROLLER_CHANNEL_ID)
        if not channel:
            print("Controller channel not found.")
            return

        panel_msg = None
        if self.panel_message_id:
            try:
                panel_msg = await channel.fetch_message(self.panel_message_id)
            except discord.NotFound:
                panel_msg = None

        if not panel_msg:
            embed = discord.Embed(
                title="Bot Control Panel",
                description="Use the buttons below to send announcements.",
                color=discord.Color.blurple()
            )
            embed.set_image(url=GIFS["online"])
            sent_msg = await channel.send(embed=embed, view=ControlPanelView())
            self.panel_message_id = sent_msg.id
            with open(CONTROL_PANEL_MSGID_FILE, "w") as f:
                f.write(str(sent_msg.id))

    @commands.command(name="control")
    async def control_command(self, ctx):
        """Recreate control panel in controller channel only."""
        if ctx.channel.id != CONTROLLER_CHANNEL_ID:
            await ctx.reply("❌ This command can only be used in the control panel channel.")
            return

        embed = discord.Embed(
            title="Bot Control Panel",
            description="Use the buttons below to send announcements.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIFS["online"])
        sent_msg = await ctx.send(embed=embed, view=ControlPanelView())
        self.panel_message_id = sent_msg.id
        with open(CONTROL_PANEL_MSGID_FILE, "w") as f:
            f.write(str(sent_msg.id))
        await ctx.reply("✅ Control panel recreated.")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions."""
        if not interaction.type == discord.InteractionType.component:
            return

        action_id = interaction.data.get("custom_id")
        user = interaction.user
        announcement_channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)

        if action_id in ["btn_online", "btn_restart"]:
            key = action_id.replace("btn_", "")
            if announcement_channel:
                embed = discord.Embed(
                    description=ANNOUNCEMENTS[key],
                    color=discord.Color.green() if key == "online" else discord.Color.orange()
                )
                await announcement_channel.send(embed=embed)
            await log_action(self.bot, user, key.title())

            # Respond first
            await interaction.response.send_message(f"{key.title()} announcement sent!", ephemeral=True)

            # Then update the GIF
            await self.update_control_panel_embed(key)

        elif action_id == "btn_dev_mode":
            await interaction.response.send_modal(TimeModal(self.bot, "dev_mode", self.update_control_panel_embed))

        elif action_id == "btn_custom_restart":
            await interaction.response.send_modal(TimeModal(self.bot, "custom_restart", self.update_control_panel_embed))


async def setup(bot):
    await bot.add_cog(ControlCog(bot))
