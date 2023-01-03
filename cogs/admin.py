from logging42 import logger
import nextcord
from nextcord.ext import commands
import yaml
import mysql.connector

class Admin(commands.Cog):
    def __init__(self, bot):
        self.client = bot

    with open("config/config.yml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    logger.info(f'CONFIG.yml:\n{cfg}')
    TESTING_GUILD_ID=cfg["discord"]["testing_guild"]
    # Database
    logger.debug("Logging into DB from admin.py")
    import mysql.connector
    self.sql = mysql.connector.connect(
        host=cfg["mysql"]["host"],
        user=cfg["mysql"]["user"],
        password=cfg["mysql"]["pass"],
        database=cfg["mysql"]["db"]
    )
    cursor = sql.cursor()

    # Load bot owner from yaml
    self.botowner = cfg["discord"]["owner"]

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('Loaded cog admin.py')

    # Commands
    @nextcord.slash_command(guild_ids=[TESTING_GUILD_ID])
    async def admin(self, interaction: nextcord.Interaction, cfg=cfg):
        pass
        # This command is to set up the following as subcommands
    
    @admin.subcommand(description="Add an administrator")
    async def add(self, interaction: nextcord.Interaction, user: nextcord.Member):
        if interaction.user.id == self.botowner:
            cursor = self.sql.cursor()
            try:
                cursor.execute(f"INSERT INTO admins (id, permission) VALUES ('{user.id}', 1);")
                await interaction.send(f"Added {user.mention} as an admin.")
            except Exception as ex:
                await interaction.send(f'**An Error occured:**\n```\n{ex}\n```\nPlease contact the devs.')
            logger.debug(f'{interaction.user.name} added {user.name}')
        else:
            await interaction.send(cfg["messages"]["noperm"], ephemeral=True)

def setup(bot):
    bot.add_cog(Admin(bot))
    logger.debug('Setup cog "admin"')