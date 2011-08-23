########### GUI2Exe SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### GUI2Exe SVN repository information ###################

# Start the imports

import wx
# We are going to use bsddb. Robin, do you recognize it? :-D
import bsddb
# We also use cPickle and zlib for maximum data compression
import cPickle
import zlib
import copy
# For the database backup
import os
import shutil

# Get the I18N things
_ = wx.GetTranslation

# Pick the highst protocol for picking, as we are not storing megabites of data
PICKLE_PROTOCOL = cPickle.HIGHEST_PROTOCOL
COMPRESSION_LEVEL = 9

# Define a couple of auxiliary functions to compress/decompress data
def serialize(obj):
    """ Compresses the data using cPickle and zlib. """
    return zlib.compress(cPickle.dumps(obj, PICKLE_PROTOCOL), COMPRESSION_LEVEL)

def deserialize(s):
    """ Decompresses the data using cPickle and zlib. """
    return cPickle.loads(zlib.decompress(s))


class DataBase(object):
    """
    A simple class which holds all the operations related to our bsddb database,
    """

    def __init__(self, mainFrame, dbName="GUI2Exe_Database.db"):
        """
        Default class constructor.

        
        **Parameters:**

        * mainFrame: the GUI2Exe main frame;
        * dbName: the database file name.
        """

        # Create a fresh database, or open an  existing one
        self.db = bsddb.btopen(dbName, "c")
        # Store a reference to the main GUI2Exe frame
        self.MainFrame = mainFrame
        # Store a reference to the database file name
        self.dbName = dbName
        self.hasError = False
        
        # Populate the project tree control in background
        try:
            self.CreateProjectTree()
            # Remove the backup database
            self.RemoveBackup()
            self.CreateBackup()
        except:
            # Database error, maybe we had a hard crash before
            self.db.close()
            self.MainFrame.SendMessage(1, _("Database file is corrupted: using backup file"))
            if self.CheckBackup():
                # Ok, the backup database works...
                self.CreateProjectTree()
                self.RemoveBackup()
                self.CreateBackup()
            else:
                # Ahi, this shouldn't happen
                self.hasError = True
        

    # ========================== #
    # Methods called in __init__ #
    # ========================== #
    
    def CreateProjectTree(self):
        """ Reads the database keys and sends them to the project tree control. """

        # Retrieve the keys from the database
        keys = self.db.keys()
        # Send the key to the project tree control
        self.MainFrame.projectTree.PopulateTree(keys)
        

    def RemoveBackup(self):
        """ Removes the existing backup database (if any). """

        backup = self.dbName + ".bak"
        if os.path.isfile(backup):  
            os.remove(backup)
            

    def CreateBackup(self):
        """ Creates a backup file for the database. """

        backup = self.dbName + ".bak"
        if os.path.isfile(backup):
            # That shouldn't happen...
            os.remove(backup)
            
        shutil.copyfile(self.dbName, backup)


    def CheckBackup(self):
        """ Checks the backup file. """

        try:
            # Let's see if the backup is fine...
            db = bsddb.btopen(self.dbName+".bak", "c")
            keys = db.keys()
            db.close()
            os.remove(self.dbName)
            shutil.copy(self.dbName+".bak", self.dbName)
            self.db = bsddb.btopen(self.dbName, "c")
            return True
        except:
            # The backup database is corrupted... bad news
            return False
        
        
    # ================= #
    # Auxiliary methods #
    # ================= #
    
    def SaveProject(self, project):
        """
        Saves the data into the database.

        
        **Parameters:**

        * project: the project to be saved.
        """

        # Get the project name
        key = project.GetName().encode()
        # Compress the data and store it
        self.db[key] = serialize(project)


    def LoadProject(self, projectName):
        """
        Loads the project from the database.

        
        **Parameters:**

        * projectName: the project name
        """

        return deserialize(self.db[projectName.encode()])


    def DeleteProject(self, project):
        """
        Deletes the project from the database.

        
        **Parameters:**

        * project: the project to be deleted.
        """

        if not isinstance(project, basestring):
            projectKey = project.GetName().encode()
        else:
            projectKey = project.encode()
            
        # Look if the database knows about this project
        if self.db.has_key(projectKey):
            del self.db[projectKey]


    def RenameProject(self, oldName, newName):
        """
        Renames the project after a user has edited the project tree control.

        
        **Parameters:**

        * oldName: the old project name;
        * newName: the new project name.
        """

        if not self.db.has_key(oldName.encode()):
            # This project has never been saved in the database
            return None
        
        # Load the project        
        tempProject = self.LoadProject(oldName.encode())
        # Set the new name for the project
        tempProject.SetName(newName.encode())
        # Store the renamed project in the database
        self.db[newName.encode()] = serialize(copy.deepcopy(tempProject))

        # Delete the old key        
        del self.db[oldName.encode()]

        return tempProject        


    def CopyProject(self, existingProject, newName):
        """
        Copies an existing project configuration into a new project.

        
        **Parameters:**

        * existingProject: the existing project to be copied;
        * newName: the new project name.
        """

        # Store the existing project configuration into the new project
        newProject = copy.deepcopy(existingProject)
        newProject.SetName(newName.encode())
        self.db[newName.encode()] = serialize(newProject)
            

    def IsProjectExisting(self, project):
        """
        Checks if a project exists in the database.

        
        **Parameters:**

        * project: the project to be checked for existance.
        """

        return self.db.has_key(project.GetName().encode())

    
    def CloseSession(self):
        """ Closes the database, flushing it before. """

        # Synchronize the database
        self.db.sync()
        # Close the session
        self.db.close()
        # Remove the backup file
        self.RemoveBackup()

