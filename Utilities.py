# Start the imports

import os
import time
import wx

# For the version checking
import urllib
from threading import Thread

from UserDict import UserDict
from Constants import ListType

# This class keeps an ordered dictionary
class odict(UserDict):
    """ An ordered dictionary implementation. """    
    def __init__(self, dict=None):
        """ Default class constructor. """

        self._keys = []
        UserDict.__init__(self, dict)


    def __delitem__(self, key):

        UserDict.__delitem__(self, key)
        self._keys.remove(key)

    def __setitem__(self, key, item):

        UserDict.__setitem__(self, key, item)
        if key not in self._keys: self._keys.append(key)


    def clear(self):

        UserDict.clear(self)
        self._keys = []


    def copy(self):

        dict = UserDict.copy(self)
        dict._keys = self._keys[:]
        return dict


    def items(self):

        return zip(self._keys, self.values())


    def keys(self):

        return self._keys


    def popitem(self):

        try:
            key = self._keys[-1]
        except IndexError:
            raise KeyError('dictionary is empty')

        val = self[key]
        del self[key]

        return (key, val)


    def setdefault(self, key, failobj=None):

        UserDict.setdefault(self, key, failobj)
        if key not in self._keys: self._keys.append(key)


    def update(self, dict):

        UserDict.update(self, dict)
        for key in dict.keys():
            if key not in self._keys: self._keys.append(key)


    def values(self):

        return map(self.get, self._keys)


class ConnectionThread(Thread):
    """Worker Thread Class."""
    def __init__(self, notifyWindow):
        """ Init Worker Thread Class. """
        Thread.__init__(self)

        self._notifyWindow = notifyWindow
        self.setDaemon(True)
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()
        

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread. Simulation of
        # a long process (well, 10s here) as a simple loop - you will
        # need to structure your processing so that you periodically
        # peek at the abort variable

        try:
            # Try to read my web page
            url = "http://xoomer.alice.it/infinity77/main/GUI2Exe.html"
            infinityPage = urllib.urlopen(url)
            text = infinityPage.read()
            infinityPage.close()
            wx.CallAfter(self._notifyWindow.CheckVersion, text)
        except IOError:
            wx.CallAfter(self._notifyWindow.CheckVersion, None)
        except:
            wx.CallAfter(self._notifyWindow.CheckVersion, None)

        return
    

# Path and file filling (os indipendent)
def opj(path):
    """Convert paths to the platform-specific separator"""

    str = apply(os.path.join, tuple(path.split('/')))
    # HACK: on Linux, a leading / gets lost...
    if path.startswith('/'):
        str = '/' + str
    return str


def flatten(list):
    """ Internal function that flattens a ND list. """

    res = []
    for item in list:
        if type(item) == ListType:
            res = res + flatten(item)
        elif item is not None:
            res = res + [item]
    return res


def unique(list):
    """ Internal function, returning the unique elements in a list."""

    # Create a fake dictionary
    res = {}

    for item in list:
        # Loop over all the items in the list
        key, value = item
        if res.has_key(key):
            res[key].append(value)
        else:
            res[key] = [value]

    # Return the dictionary values (a list)    
    return res.items()


def setupString(key, item, isPyInstaller=False, splitter=False):
    """ Sets up the strings for py2exe. """

    # This is an incredible and horrible hack, and it may not always work     
    if key == "data_files" and not isPyInstaller:

        text = "["
        for i in xrange(len(item)):
            indent = len(key) + 9 + len(item[i][0])
            text += "('%s', "%item[i][0] + (",\n" + " "*indent).join(repr(item[i][1]).split(",")) + ")"
            if i != len(item)-1:
                text += ",\n" + " "*(len(key)+4)
        item = text + "]"

    else:
        
        indent = len(key)+3
        spacer = "\n" + " "*indent
        item = ("%s"%item).split(",")

        text = ""
        lentext = 0
        maxLen = (splitter and [100] or [60])[0]
        
        for chunk in item:
            text += chunk + ","
            lentext += len(chunk)+2
            if lentext > maxLen and chunk != item[-1]:
                text += spacer
                lentext = len(spacer)-1

        item = text[0:-1]
        
    return item


def now():
    """ Returns the current time formatted. """

    t = time.localtime(time.time())
    st = time.strftime("%d %B %Y @ %H:%M:%S", t)
    
    return st


def shortNow():
    """ Returns the current time formatted. """
    
    t = time.localtime(time.time())
    st = time.strftime("%H:%M:%S", t)

    return st


def FractSec(s):
    """ Formats time as hh:mm:ss. """
    
    min, s = divmod(s, 60)
    h, min = divmod(min, 60)
    return h, min, s


def GetExecutableData(project, compiler):
    """ Returns information about the executable file. """

    config = project[compiler]
    dist_dir = config["dist_dir"]

    if compiler == "py2exe":
        try:
            script = config["multipleexe"][0][1]
        except IndexError:
            return "", ""
        dist_dir_choice = config["dist_dir_choice"]
        if not dist_dir_choice or not dist_dir.strip():
            dist_dir = "dist"
            
    elif compiler == "PyInstaller":
        try:
            script = config["scripts"][-1]
            if config["onefile"]:
                dist_dir = ""
                script = os.path.normpath(os.path.split(script)[0] + "/" + config["exename"])
        except IndexError:
            return "", ""
    else:
        script = config["script"]

    if not script:
        return "", ""
    
    path = os.path.split(script)[0]
    exePath = os.path.normpath(path + "/" + dist_dir)

    return GetFolderSize(exePath)


def GetFolderSize(exePath):
    
    folderSize = numFiles = 0
    
    for path, dirs, files in os.walk(exePath):
        for file in files:
            filename = os.path.join(path, file)
            folderSize += os.path.getsize(filename)
            numFiles += 1

    if numFiles == 0:
        return "", ""
    
    folderSize = "%0.2f"%(folderSize/(1024*1024.0))
    numFiles = "%d"%numFiles

    return numFiles, folderSize
    

def RecurseSubDirs(directory, userDir):

    config = []
    baseStart = os.path.basename(directory)
    
    for root, dirs, files in os.walk(directory):
        start = root.find(baseStart) + len(baseStart)
        dirName = userDir + root[start:]
        dirName = dirName.replace("\\", "/")
        paths = []
        for name in files:
            paths.append(os.path.normpath(os.path.join(root, name)))

        config.append((dirName, paths))

    return config


def PrintTree(strs, tree, depth=0, written=False):
    
    if type(tree) == ListType:
        strs += setupString(" "*32, tree) + ",\n"
    elif type(tree) == bool:
        strs += "%s, \n"%str(tree)
    elif isinstance(tree, basestring):
        try:
            strs += "%d, \n"%int(tree)
        except:
            if tree.strip():
                strs += "r'%s',\n"%tree
            else:
                strs += "'',\n"
    else:
        keys = tree.keys()
        keys.sort()
        for key in keys:
            for i in range(depth):
                strs += "\t\t\t\t"
            if depth == 0:
                strs += "\t\t" + ("'%s'"%key).ljust(13) + " : {\n"
                written = True
            else:
                strs += "'%s': "%key
            strs = PrintTree(strs, tree[key],depth+1, written)
        if written and depth > 0:
            strs += "\t\t\t\t},\n\n"

    return strs
