# Start the imports

import os
import time
import wx

# For the version checking
import urllib2
from threading import Thread

# Used to recurse subdirectories
import fnmatch

from UserDict import UserDict
from Constants import ListType

# This class keeps an ordered dictionary
class odict(UserDict):
    """ An ordered dictionary implementation. """    

    def __init__(self, dict=None):
        """
        Default class constructor.

        @param dict: a dictionary from where to get the new dict keys (optional).
        """

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
    """ Worker thread class to attempt cnnection to the internet."""
    
    def __init__(self, notifyWindow):
        """
        Initialize the worker thread.

        @param notifyWindow: the window which will receive the notification when
                             this thread finishes the work.
        """
        
        Thread.__init__(self)

        self._notifyWindow = notifyWindow
        self.setDaemon(True)
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()
        

    def run(self):
        """ Run worker thread. """
        
        # This is the code executing in the new thread. Simulation of
        # a long process as a simple urllib2 call

        try:
            # Try to read my web page
            url = "http://xoomer.alice.it/infinity77/main/GUI2Exe.html"
            infinityPage = urllib2.urlopen(url)
            text = infinityPage.read()
            infinityPage.close()
            wx.CallAfter(self._notifyWindow.CheckVersion, text)
        except IOError:
            # Unable to get to the internet
            wx.CallAfter(self._notifyWindow.CheckVersion, None)
        except:
            # Some other strange error...
            wx.CallAfter(self._notifyWindow.CheckVersion, None)

        return
    

# Path and file filling (os indipendent)
def opj(path):
    """
    Converts paths to the platform-specific separator.

    @param path: the path to be normalized.
    """

    str = apply(os.path.join, tuple(path.split('/')))
    # HACK: on Linux, a leading / gets lost...
    if path.startswith('/'):
        str = '/' + str
    return str


def flatten(list):
    """
    Internal function that flattens a N-D list.

    @param list: the N-D list that needs to be flattened.
    """

    res = []
    for item in list:
        if type(item) == ListType:
            res = res + flatten(item)
        elif item is not None:
            res = res + [item]
    return res


def unique(list):
    """
    Internal function, returning the unique elements in a list.

    @param list: the list for which we want the unique elements.
    """

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
    """
    Sets up the strings for py2exe and other compilers.

    @param key: the option name (data_files, includes, etc...);
    @param item: the option value (usually a list);
    @param isPyInstaller: whether we are compiling with PyInstaller or not
                          (PyInstaller requires a different syntax);
    @param splitter: currently unused.
    """

    # This is an incredible and horrible hack, and it may not always work     
    if key == "data_files" and not isPyInstaller:
        # Set up the data_files option
        text = "["
        for i in xrange(len(item)):
            indent = len(key) + 9 + len(item[i][0])
            text += "('%s', "%item[i][0] + (",\n" + " "*indent).join(repr(item[i][1]).split(",")) + ")"
            if i != len(item)-1:
                text += ",\n" + " "*(len(key)+4)
        item = text + "]"

    else:
        # Split the string item and try to text-wrap it
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
    """
    Formats time as hh:mm:ss.

    @param s: the number of seconds.
    """
    
    min, s = divmod(s, 60)
    h, min = divmod(min, 60)
    return h, min, s


def GetExecutableData(project, compiler):
    """
    Returns information about the executable file.

    @param project: the project being compiled;
    @param compiler: the compiler used to build the project.
    """

    if not project.GetBuildOutput(compiler):
        # Project hasn't been compiled yet
        return "", ""
    
    try:
        exePath = project.GetDistDir(compiler)
    except:
        # Project hasn't been compiled
        return "", ""
    
    return GetFolderSize(exePath)


def GetFolderSize(exePath):
    """
    Returns the size of the executable distribution folder.

    @param exePath: the path of the distribution folder.
    """
    
    folderSize = numFiles = 0
    join, getsize = os.path.join, os.path.getsize
    # Recurse over all the folders and sub-folders    
    for path, dirs, files in os.walk(exePath):
        for file in files:
            # Get the file size
            filename = join(path, file)
            folderSize += getsize(filename)
            numFiles += 1

    if numFiles == 0:
        # No files found, has the executable ever been built?
        return "", ""
    
    folderSize = "%0.2f"%(folderSize/(1024*1024.0))
    numFiles = "%d"%numFiles

    return numFiles, folderSize
    

def RecurseSubDirs(directory, userDir, extensions):
    """
    Recurse one directory to include all the files and sub-folders in it.

    @param directory: the folder on which to recurse;
    @param userDir: the directory chosen by the user;
    @param extensions: the file extensions to be filtered.
    """

    config = []
    baseStart = os.path.basename(directory)

    normpath, join = os.path.normpath, os.path.join
    splitext, match = os.path.splitext, fnmatch.fnmatch
    
    # Loop over all the sub-folders in the top folder 
    for root, dirs, files in os.walk(directory):
        start = root.find(baseStart) + len(baseStart)
        dirName = userDir + root[start:]
        dirName = dirName.replace("\\", "/")
        paths = []
        # Loop over all the files
        for name in files:
            # Loop over all extensions
            for ext in extensions:
                if match(name, ext):
                    paths.append(normpath(join(root, name)))
                    break

        if paths:
            config.append((dirName, paths))

    return config


def PrintTree(strs, tree, depth=0, written=False):
    """
    Prints a tree-dict structure into a string.

    @param strs: the string to which to print the tree,
    @param depth: the nesting level we reached in the dictionary;
    @param written: whether the dict key has been written or not.
    """
    
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

