from logging42 import logger
import yaml
import itertools
import sys

class Database:
    """ Fetch & Write information to/from from Database """
    def __init__(self, guild, reason='No Reason Specified'):
        self.guild = guild
        self.reason = reason
        # Load Yaml
        with open("config/config.yml", "r") as ymlfile:
            self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        with open("config/settings.yml", "r") as ymlfile:
            self.settings = yaml.load(ymlfile, Loader=yaml.FullLoader)
        if self.cfg['storage'] == 'sqlite':
            self.connect('init')

    # Functions
    # Connect to DB
    @logger.catch
    def connect(self, subreason):
        # Connect to Database
        if self.cfg["storage"] == "sqlite":
            import sqlite3
            sql = sqlite3.connect('storage.db')
            self.sql = sql
            self.cursor = sql.cursor()
            self.db_type = 'sqlite'
            self.current_database = sqlite3
        elif self.cfg["storage"] == "mysql":
            import mysql.connector
            sql = mysql.connector.connect(
                host=self.cfg["mysql"]["host"],
                user=self.cfg["mysql"]["user"],
                password=self.cfg["mysql"]["pass"],
                database=self.cfg["mysql"]["db"]
            )
            self.cursor = sql.cursor()
            self.db_type = 'mysql'
            self.current_database = mysql
        else:
            logger.critical('Invalid storage type! Please edit the "storage" option in config/config.yml to either "mysql" or "sqlite" depending on which database you intend to use.')
            sys.exit(1)
        logger.info(f'Connected to {self.db_type} database in {subreason} for {self.reason}')
    # Create database tables
    @logger.catch
    def create(self, table=None):
        """ Create Tables for Database required for every guild """
        if self.cfg['storage'] == 'mysql':
            self.connect('create')
        if table == 'admins' or table == None:
            self.cursor.execute(f'CREATE TABLE IF NOT EXISTS admins_{self.guild.id} ( id int, admin bit );')
            if self.db_type == 'sqlite':
                self.sql.commit()
            logger.info(f'Created table "admins_{self.guild.id}", if it doesnt already exist!')
        if table == 'settings' or table == None:
            self.cursor.execute(f'CREATE TABLE IF NOT EXISTS settings_{self.guild.id} ( setting string, value string );')
            for setting in self.settings['settings']:
                self.cursor.execute(f'INSERT INTO settings_{self.guild.id} ( setting, value ) VALUES ( "{setting}", "none" );')
            if self.db_type == 'sqlite':
                self.sql.commit()
            logger.info(f'Created table "settings_{self.guild.id}", if it doesnt already exist!')
    # Verify database exists and is correctly setup
    @logger.catch
    def verify(self, tables=True, repair=True):
        """ Make sure tables exist, and create them if they dont """
        if self.cfg['storage'] == 'mysql':
            self.connect('verify')
        if tables:
            admins_exists = False
            settings_exists = False
            if self.db_type == 'sqlite':
                existing = self.cursor.execute('select name from sqlite_schema where type="table" and name not like "sqlite_%";')
            else:
                existing = self.cursor.execute('select * from information_schema.tables;').fetchall()
            if f'admins_{self.guild.id}' in existing:
                admins_exists = True
            if f'settings_{self.guild.id}' in existing:
                settings_exists = True
            if self.db_type == 'sqlite':
                self.sql.commit()
        if repair:
            settings_absent = []
            amend_settings = False
            try:
                tup = self.cursor.execute(f'SELECT setting FROM settings_{self.guild.id};').fetchall()
            except self.current_database.OperationalError:
                self.create('settings')
                tup = self.cursor.execute(f'SELECT setting FROM settings_{self.guild.id};').fetchall()
            existing = list(itertools.chain(*tup))
            for setting in self.settings['settings']:
                if setting in existing:
                    pass
                else:
                    amend_settings = True
                    settings_absent.append(setting)
            if amend_settings:
                for setting in settings_absent:
                    self.cursor.execute(f'INSERT INTO settings_{self.guild.id} ( setting, value ) VALUES ( "{setting}", "none" )')
                if self.db_type == 'sqlite':
                    self.sql.commit()
        if not admins_exists and repair:
            logger.warning(f'Created admins table for guild {self.guild.id} because it did not exist!')
            self.create(table='admins')
        if not settings_exists and repair:
            logger.warning(f'Created settings table for guild {self.guild.id} because it did not exist!')
            self.create(table='settings')

    # Fetch information from DB
    # Default to settings if no table is specified
    @logger.catch
    def fetch(self, setting, return_list=False, admin=False):
        """ Fetch information from Database """
        if self.cfg['storage'] == 'mysql':
            self.connect('fetch')
        if admin or setting == 'admins':
            if return_list:
                try:
                    tup = self.cursor.execute(f'SELECT * FROM "admins_{self.guild.id}";').fetchall()
                except self.current_database.OperationalError:
                    self.create()
                    tup = self.cursor.execute(f'SELECT * FROM "admins_{self.guild.id}";').fetchall()
                admin_list = list(itertools.chain(*tup))
                admin_list.remove(1)
                return admin_list
            else:
                return self.cursor.execute(f'SELECT id FROM admins_{self.guild.id} WHERE id={setting};').fetchone()
        else:
            self.cursor.execute(f'SELECT enabled FROM settings_{self.guild.id} WHERE setting={setting};')
            if return_list:
                tup = self.cursor.fetchall()
                return list(itertools.chain(*tup))
            else:
                return self.cursor.fetchone()

            
    # Change information in DB
    # Should ALWAYS return true if successfull, false if an error occurred
    @logger.catch
    def set(self, setting, value, clear=False):
        """ Set values within the Database. Returns true if successful.
        If value is None, an admin will be removed or a setting will be set to none """
        if self.cfg['storage'] == 'mysql':
            self.connect('set')
        if setting == 'admin' and clear == True:
            try:
                self.cursor.execute(f'DELETE FROM admins_{self.guild.id} WHERE id IS {value}')
                logger.info(f'Removed id {value} from table admins_{self.guild.id}')
                return True
            except:
                logger.warning(f'Failed to delete ID {value} from table admins_{self.guild.id}!')
                return False
        elif setting == 'admin':
            try:
                self.cursor.execute(f'INSERT INTO admins_{self.guild.id} ( id, admin ) VALUES ( {value}, 1 )')
                logger.info(f'Added id {value} to table admins_{self.guild.id}')
                return True
            except:
                logger.warning(f'Failed to add id {value} to table admins_{self.guild.id}!')
                return False
        elif clear == True:
            try:
                self.cursor.execute(f"UPDATE settings_{self.guild.id} SET enabled = (CASE WHEN setting = '{setting}' THEN enabled = 'none'")
                logger.info(f'Set {setting} to {value} for table settings_{self.guild.id}')
                return True
            except:
                logger.warning(f'Failed to set value {setting} to {value} for table settings_{self.guild.id}!')
                return False
        else:
            try:
                self.cursor.execute(f"UPDATE settings_{self.guild.id} SET enabled = (CASE WHEN setting = '{setting}' THEN enabled = '{value}'")
                logger.info(f'Set {setting} to {value} for table settings_{self.guild.id}')
                return True
            except:
                logger.warning(f'Failed to set value {setting} to {value} for table settings_{self.guild.id}!')
                return False
    
    # Send raw commands to Database
    @logger.catch
    def raw(self, command, fetchall=True, fetchone=False):
        """ Send a raw SQL query to the SQL server 
        remember to use the correct table, admins_{self.guild.id} or settings_{self.guild.id}
        Options: fetchall - use `.fetchall()` method and return result (default True)
                 fetchone - use `.fetchone()` method and return result (default False)
                 If both are false, execute bare command and return true if successful """
        if self.cfg['storage'] == 'mysql':
            self.connect('raw')
        try:
            if fetchone:
                return self.cursor.execute(command).fetchone()
            elif fetchall:
                return self.cursor.execute(command).fetchall()
            else:
                self.cursor.execute(command)
                return True
        except self.current_database.OperationalError:
            logger.warning(f'OperationalError when running raw command: "{command}"!')
            return False
    
    # Delete tables of a guild
    @logger.catch
    def delete(self, settings=True, admins=True):
        """ Completely delete a guild's data """
        if self.cfg['storage'] == 'mysql':
            self.connect('delete')
        if settings:
            self.cursor.execute(f'drop table "settings_{self.guild.id}";')
            logger.debug(f'Deleted table settings_{self.guild.id}.')
        if admins:
            self.cursor.execute(f'drop table "admins_{self.guild.id}";')
            logger.debug(f'Deleted table admins_{self.guild.id}')
        return True


    # Properly close DB
    @logger.catch
    def close(self):
        """ Close the Database, if necessary """
        if self.db_type == 'sqlite':
            self.sql.commit()
            self.sql.close()
            logger.debug(f'Closed sqlite3 database connection reasoned "{self.reason}".')
            return True
        else:
            return True