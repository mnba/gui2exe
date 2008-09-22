# Start the imports

import sys
import os
from Utilities import odict, opj, now


class Project(odict):

    def __init__(self, configuration=None, name=""):
        """
        Default class constructor.

        @param configuration: the project data
        @param name: the project name as entered by the user

        """        

        # Initialize the ordered dictionary
        # "Project" is a dictionary of dictionaries: the top level keys specify
        # which compiler the children keys refer to (i.e., py2exe, py2app etc...)
        # and for every top level key the secondary dictionary contains the
        # project configuration as entered by the user
        odict.__init__(self, configuration)

        # Store the data we are going to need later        
        self.name = name
        self.creationDate = now()
        self.customCode = {}
        self.postCompile = {}
        self.hasBeenCompiled = False
        self.missingModules = []
        self.binaryDependencies = []
        self.buildOutputs = {}


    def Update(self, compiler, keyName, keyValue):
        """ Updates the project with data inserted by the user. """

        self[compiler][keyName] = keyValue
                

    def SetConfiguration(self, compiler, configuration):
        """ Sets a whole configuration for the selected compiler. """

        self[compiler] = configuration


    def GetConfiguration(self, compiler):
        """ Returns the configuration for the selected compiler. """

        return self[compiler]


    def SetName(self, name):
        """ Sets the project name. """

        self.name = name
        

    def GetName(self):
        """ Returns the project name. """

        return self.name


    def GetCreationDate(self):
        """ Returns the project creation date. """

        return self.creationDate
    

    def SetCustomCode(self, compiler, code):
        """ Sets the custom code entered by the user. """

        if isinstance(self.customCode, basestring):
            self.customCode = {}
            
        self.customCode[compiler] = code

        
    def GetCustomCode(self, compiler):
        """ Returns the custom code entered by the user. """

        if isinstance(self.customCode, basestring):
            tmp = self.customCode[:]
            self.customCode = {}
            self.customCode[compiler] = tmp

        if compiler not in self.customCode:
            return ""

        return self.customCode[compiler]


    def SetPostCompileCode(self, compiler, code):
        """ Sets some custom post-compilation code to be executed. """

        if not hasattr(self, "postCompile"):
            self.postCompile = {}
            
        self.postCompile[compiler] = code
        

    def GetPostCompileCode(self, compiler):
        """ Returns the custom post-compilation code to be executed (if any). """

        if not hasattr(self, "postCompile"):
            self.postCompile = {}
            
        if compiler not in self.postCompile:
            return ""
        
        return self.postCompile[compiler]


    def SetCompilationData(self, missingModules, binaryDependencies):
        """
        Sets the results of the compilation process, in terms of what the compiler
        says are the binary dependencies (dlls) and the missing modules (Python files).
        """

        self.missingModules = missingModules
        self.binaryDependencies = binaryDependencies


    def GetCompilationData(self):
        """ Returns the result of the compilation process. """

        return self.missingModules, self.binaryDependencies


    def HasBeenCompiled(self):
        """ Checks if a project has been compiled or not. """

        return self.hasBeenCompiled


    def GetExecutableName(self, compiler):
        """ Returns the executable name based on the chosen compiler. """

        distDir = True
        extension = (sys.platform == "win32" and [".exe"] or [""])[0]
        configuration = self[compiler]
        # The executable name, for py2exe at least, lives in the folder:
        # /MainPythonFileFolder/dist_directory/
        if compiler == "py2exe":
            script, exename = configuration["multipleexe"][0][1:3]
            if exename.strip():
                script = os.path.normpath(os.path.split(script)[0] + "/" + exename)
            dist_dir_choice = configuration["dist_dir_choice"]
            dist_dir = configuration["dist_dir"]
            if not dist_dir_choice or not dist_dir.strip():
                distDir = False
                script = os.path.normpath(os.path.split(script)[0] + "/dist/" + exename)
                
        elif compiler == "PyInstaller":
            # This is not 100% guaranteed to succeed...
            script = configuration["scripts"][-1]
            exename = configuration["exename"]
            if exename.strip():
                script = os.path.normpath(os.path.split(script)[0] + "/" + exename)
            if configuration["onefile"]:
                distDir = False

        elif compiler == "cx_Freeze":
            script = configuration["script"]
            distChoice = configuration["dist_dir_choice"]
            targetChoice = configuration["target_name_choice"]
            exename = configuration["target_name"]
            dist_dir = configuration["dist_dir"]
            dist_dir = ((distChoice and dist_dir.strip()) and [dist_dir.strip()] or ["dist"])[0]

            if exename.strip() and targetChoice:
                script = os.path.normpath(os.path.split(script)[0] + "/" + exename)

        elif compiler == "py2app":
            script = configuration["script"]
            extension = configuration["extension"]
            distChoice = configuration["dist_dir_choice"]
            dist_dir = configuration["dist_dir"]
            if not dist_dir_choice or not dist_dir.strip():
                distDir = False
            
        else:
            distChoice = configuration["dist_dir_choice"]
            dist_dir = configuration["dist_dir"]
            dist_dir = ((distChoice and dist_dir.strip()) and [dist_dir.strip()] or ["dist"])[0]

            script = configuration["script"]
                
        if distDir:
            path, script = os.path.split(script)
            script = os.path.splitext(script)[0] + extension
            exePath = os.path.normpath(path + "/" + dist_dir + "/" + script)
        else:
            exePath = script

        return os.path.normpath(exePath)


    def GetManifestFileName(self, compiler):
        """ Returns the manifest file name for Windows XP executables. """

        configuration = self[compiler]
        if "create_manifest_file" not in configuration:
            # No such thing for py2exe, py2app
            return

        addManifest = configuration["create_manifest_file"]
        if not bool(int(addManifest)):
            # User has not requested it
            return

        extension = ".exe.manifest"
        programName = None

        if compiler == "cx_Freeze":
            if configuration["base"] != "windows":
                # it's not a windowed application
                return
            
            script, dist_dir, target = configuration["script"], configuration["dist_dir"], \
                                       configuration["target_name"]

            dirName, fileName = os.path.split(script)
            fileNoExt, ext = os.path.splitext(script)
            singleFileNoExt = os.path.split(fileNoExt)[1]
            
            if not target.strip():
                programName = singleFileNoExt
                if not dist_dir.strip():
                    manifest = fileNoExt + extension
                else:
                    manifest = os.path.normpath(dirName + "/" + dist_dir + "/" + singleFileNoExt + extension)
            else:
                programName = target.replace(".exe", "").strip()
                if not dist_dir.strip():
                    manifest = os.path.normpath(dirName + "/dist/" + target.strip() + extension[4:])
                else:
                    manifest = os.path.normpath(dirName + "/" + dist_dir + "/" + target.strip() + extension[4:])

        elif compiler == "PyInstaller":
            script, dist_dir, target = configuration["scripts"][-1], configuration["dist_dir"], \
                                       configuration["exename"]
            onefile = configuration["onefile"]
            dirName, fileName = os.path.split(script)
            fileNoExt, ext = os.path.splitext(script)
            singleFileNoExt = os.path.split(fileNoExt)[1]
            if onefile:
                programName = target.replace(".exe", "")
                manifest = os.path.normpath(dirName + "/" + target.replace(".exe", "") + extension)
            else:
                programName = singleFileNoExt
                manifest = os.path.normpath(dirName + "/" + dist_dir + "/" + singleFileNoExt + extension)
                
        else:

            script, dist_dir = configuration["script"], configuration["dist_dir"]
            dirName, fileName = os.path.split(script)
            fileNoExt, ext = os.path.splitext(script)
            singleFileNoExt = os.path.split(fileNoExt)[1]
            if dist_dir.strip():
                manifest = os.path.normpath(dirName + "/" + dist_dir + "/" + singleFileNoExt + extension)
            else:
                manifest = os.path.normpath(dirName + "/dist/" + singleFileNoExt + extension)
            programName = singleFileNoExt
            
        return manifest, programName


    def AssignBuildOutput(self, compiler, outputText):
        """ Assigns the full build output text to the project for later viewing. """

        if not hasattr(self, "buildOutputs"):
            self.buildOutputs = {}

        outputText = now() + "/-/-/\n" + outputText
        self.buildOutputs[compiler] = outputText


    def GetBuildOutput(self, compiler):
        """ Retrieves the full build output text (if any). """
        
        if not hasattr(self, "buildOutputs"):
            self.buildOutputs = {}
            return ""

        if compiler not in self.buildOutputs:
            return ""
        
        return self.buildOutputs[compiler]

    
    def GetDistDir(self, compiler):
        """ Retrieves the distribution directory for the specific compiler. """

        exeName = self.GetExecutableName(compiler)
        return os.path.split(exeName)[0]

    
