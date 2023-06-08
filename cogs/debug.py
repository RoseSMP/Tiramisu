# 
# Tiramisu Discord Bot
# --------------------
# Debugging Utilities
# 
from logging42 import logger
import nextcord
from nextcord.ext import commands
import yaml

from libs.database import Database
from libs import buttons

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    with open("config/config.yml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    TESTING_GUILD_ID=cfg["discord"]["testing_guild"]

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('Loaded cog debug.py')

    bot = commands.Bot()

    # Commands
    @nextcord.slash_command(description='Commands for Debugging', guild_ids=[TESTING_GUILD_ID])
    async def debug(self, interaction: nextcord.Interaction):
        pass

    @debug.subcommand(description="Print DB")
    async def db(self, interaction: nextcord.Interaction, settings=False):
        db = Database(interaction.guild, reason='Fetch for debugging')
        if settings:
            t_type = 'settings'
            table = db.raw(f'select * from "settings_{db.guild.id}";')
        else:
            t_type = 'admins'
            table = db.fetch('admins')
        if table == False:
            table = 'Failed to fetch from database! OperationalError!'
            logger.warning('Failed to fetch data from database!')
        else:
            logger.debug(f"Printing db contents for {interaction.user.name}.")
        if t_type == 'admins':
            await interaction.response.send_message(f"Found these values in table `{t_type}_{db.guild.id}`: ```\n{table} ```\nType: `{type(table)}`\
                \nAre you (`{interaction.user.id}`) in list?: `{interaction.user.id in table}`")
        else:
            await interaction.response.send_message(f"Sending data to log")
            logger.info(f'Found this data in "{t_type}_{db.guild.id}":\n{table}')
        db.close()
    
    @debug.subcommand(description='Show a list of all members')
    async def members(self, interaction: nextcord.Interaction):
        message = '**List Of all Members:**'
        for user in interaction.guild.humans:
            message += f'\n • {user.name}#{user.discriminator} ({user.display_name}) ID: `{user.id}`'
        await interaction.send(message)

    @nextcord.slash_command(description='Test buttons')
    async def button(self, interaction: nextcord.Interaction):
        await interaction.send('Creating button...')
        await buttons.HelloButton().start(interaction=interaction)

def setup(bot):
    bot.add_cog(Debug(bot))
    logger.debug('Setup cog "debug"')