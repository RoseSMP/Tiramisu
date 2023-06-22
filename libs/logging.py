# 
# Tiramisu Discord Bot
# --------------------
# Logging for Moderators
# 
import nextcord
from libs.database import Database

class LoggingEvent:
    def __init__(self, guild: nextcord.Guild, title: str, user: nextcord.User, extra: dict = {}):
        """ Base class for logging events
        Parameters:
         - `guild`: nextcord.Guild, the guild this is happening in
         - `title`: str, the heading for the log message
         - `user`: nextcord.User, the doer of the action
         - `extra`: optional dict, fields for the message """

        self.guild = guild
        self.title = title
        self.user = user
        self.extra = extra
        self.void = False # Used to check if an action should be logged
    
    def message(self):
        msg = f"{self.title}\nAuthor: {self.user.name} `{self.user.id}`"
        for key in self.extra:
            msg += f"\n{key}: {self.extra[key]}"
        return msg

class DeletedMessage(LoggingEvent):
    def __init__(self, message: nextcord.Message):
        """ Event for a message being deleted """
        attachments = ''
        for attachment in message.attachments:
            if attachments == '':
                attachments += attachment.filename
            else:
                attachments += f', {attachment.filename}'
        if attachments == '':
            attachments = 'None'

        super().__init__(
            message.guild, 
            "**🗑️ Deleted Message **", 
            message.author,
            extra = {
                "Channel":message.channel.mention,
                "Content":message.content,
                "Attachments":attachments
            }
            )

class EditedMessage(LoggingEvent):
    def __init__(self, old: nextcord.Message, new:nextcord.Message):
        """ Event for message being edited """
        super().__init__(
            old.guild,
            "**✏️ Edited Message **",
            old.author,
            extra = {
                "Channel":old.channel.mention,
                "Old Content":old.content,
                "Old Attachments":self._get_attachments(old),
                "New Content":new.content,
                "New Attachments":self._get_attachments(new)
            }
        )
    
    def _get_attachments(self, message: nextcord.Message):
        attachments = ''
        for attachment in message.attachments:
            if attachments == '':
                attachments += attachment.filename
            else:
                attachments += f', {attachment.filename}'
        if attachments == '':
            attachments = 'None'
        
        return attachments

class ChangeVoice(LoggingEvent):
    def __init__(self, member, before, after):
        """ Event for Voice state update """
        if before.channel == None and after.channel != None: # User joined a VC
            action = 'Joined'
        elif before.channel != None and after.channel == None: # User left VC
            action = 'Left'
        else:
            self.void = True
        
        super().__init__(
                member.guild, f"**🎤 {action} VC**",
                member, extra = {
                    "VC":after.channel.mention
                }
            )



async def log(event: LoggingEvent):
    db = Database(event.guild, reason='Logging, fetch `log_channel`')
    try:
        channel = event.guild.get_channel(int(db.fetch('log_channel')))
        if channel == None:
            raise ValueError
    except ValueError:
        return

    if not event.void:
        await channel.send(event.message())