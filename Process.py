# Start the imports
import os
import sys
import wx
# This is needed to create a temporary file for the compilation process
import tempfile
# I ue this only on Unix/Linux/Mac... but why Windows doesn't have os.kill?
import signal
import time

from Utilities import opj, FractSec

# Get the I18N things
_ = wx.GetTranslation


class Process(object):
    """
    A class which starts an external process to compile a Python source file
    into an executable.
    """
    
    def __init__(self, parent, buildDir, setupScript, run, compiler,
                 project, pageNumber, pythonVersion):
        """
        Default class constructor.

        
        **Parameters:**

        *  parent: the parent widget (GUI2Exe);
        * buildDir: the directory in which we build the executable;
        * setupScript: the setup file passed as a string;
        * run: if False, only a "dry-run" is performed (py2exe only);
        * compiler: the compiler used;
        * project: the project we are compiling;
        * pageNumber: the main wx.aui.AuiNotebook page number we belong to;
        * pythonVersion: the Python executable used to call the exe builder.
        """        

        # Store the input data passed in __init__
        self.MainFrame = parent
        self.buildDir = buildDir
        self.setupScript = setupScript
        self.run = run
        self.compiler = compiler
        self.project = project
        self.pageNumber = pageNumber
        self.pythonVersion = pythonVersion

        # No process started, the main frame will take care of it        
        self.process = None
        # Let's keep track if we failed the compilation step or not
        self.failed = False
        # We store all the output that comes from the process
        self.fullText = ""
        # Store the full output build messages
        self.outputText = ""
        

    def Start(self):
        """ Starts the compilation process. """

        # Change the directory to the compilation folder
        os.chdir(opj(self.buildDir))
        # Verify if it is a dry-run or a real compilation
        dryRun = (self.run and [""] or ["--dry-run"])[0]

        # Create a temporary file that we will delete later
        if self.compiler == "PyInstaller":
            suffix = ".spec"
        else:
            suffix = ".py"
            
        fd, tmpFileName = tempfile.mkstemp(suffix=suffix, dir=self.buildDir)
        # Write the setup script string in the temporary file
        fid = open(tmpFileName, "wt")
        fid.write(self.setupScript)
        fid.close()
        # Store the temporary file data
        self.tmpFileName = (fd, tmpFileName)

        # Run the setup.py optimized, if the user chose to
        configuration = self.project[self.compiler]
        optimize = ""
        if "optimize" in configuration:
            value = int(configuration["optimize"])
            if value > 0:
                optimize = "-" + "O"*value

        # Build the compilation command
        if self.compiler == "py2exe":
            cmd = '%s %s -u "%s" %s %s'%(self.pythonVersion, optimize, tmpFileName, self.compiler, dryRun)
            
        elif self.compiler == "cx_Freeze":
            distDir = configuration["dist_dir"]
            distChoice = configuration["dist_dir_choice"]
            if not distDir.strip() or not distChoice:
                distDir = "dist"
            cmd = '%s %s -u "%s" %s%s'%(self.pythonVersion, optimize, tmpFileName, "build --build-exe=", distDir)

        elif self.compiler == "bbfreeze":
            cmd = '%s %s -u "%s"'%(self.pythonVersion, optimize, tmpFileName)

        elif self.compiler == "PyInstaller":
            pyInstallerPath = self.MainFrame.GetPyInstallerPath()
            build = os.path.normpath(pyInstallerPath + "/Build.py")
            cmd = '%s %s -u "%s" "%s"'%(self.pythonVersion, optimize, build, tmpFileName)

        elif self.compiler == "py2app":
            cmd = '%s %s -u "%s" %s'%(self.pythonVersion, optimize, tmpFileName, self.compiler)

        # Monitor the elapsed time
        self.startTime = time.time()
            
        # Start the process, redirecting the output to catch stdio
        self.process = wx.Process(self.MainFrame)
        self.process.Redirect()
        # We want the process to be asynchronous
        self.pid = wx.Execute(cmd, wx.EXEC_ASYNC, self.process)


    def Kill(self):
        """ Kills the process. """

        # This doesn't work very well on Windows :-(        
        self.process.CloseOutput()
        self.process.Kill(self.pid, wx.SIGTERM, wx.KILL_CHILDREN)
        if wx.Platform in ["__WXGTK__", "__WXMAC__"]:
            try:
                os.kill(self.pid, signal.SIGTERM)
            except:
                pass
            
        self.Destroy()
        

    def Destroy(self):
        """ Destroy the process. """

        # Ok, this line is commented because if I leave it as it is Python
        # bombs with the classical Windows error dialog
        self.process.Destroy()
        
        self.MainFrame.process = None
        # Close the temporary file
        os.close(self.tmpFileName[0])
        # Remove the temporary file from the compilation directory
        if os.path.isfile(opj(self.tmpFileName[1])):
            try:
                os.remove(opj(self.tmpFileName[1]))
            except:
                # Something is keeping it open... skip for now
                pass

        # Returns to the installation directory            
        os.chdir(self.MainFrame.installDir)

        
    def HandleProcessMessages(self, processEnded=False):
        """
        Handles all the messages that come from input and error streams.

        
        **Parameters:**

        * processEnded: whether the process has just ended.
        """

        # Get the input stream
        istream = self.process.GetInputStream()
        self.ReadStream(istream, 0, processEnded)
        # Get the error stream
        estream = self.process.GetErrorStream()
        self.ReadStream(estream, 1, processEnded)

        if processEnded and not self.failed:
            # Process finished without errors, send a congratulation message
            self.MainFrame.SendMessage(0, _("Setup file succesfully compiled"))
            # Show the elapsed time
            h, m, s = FractSec(int(time.time() - self.startTime))
            self.MainFrame.SendMessage(0, _("Elapsed time for the process:") + " %02d:%02d:%02d"%(h, m, s))
            # Update visually the project page
            self.MainFrame.UpdatePageBitmap(self.project.GetName(), 1, self.pageNumber)
            # Process the output text from the compilation steps
            self.ProcessOutputText()
            if self.run:
                # Create a manifest file if needed
                self.MainFrame.CreateManifestFile(self.project, self.compiler)
                # It was a real compilation, ask the user to test the executable
                self.MainFrame.SuccessfulCompilation(self.project, self.compiler)

        if processEnded:
            # Store the full output message in the project page
            self.project.AssignBuildOutput(self.compiler, self.outputText)


    def ReadStream(self, stream, isError, processEnded):
        """
        Reads the input/error streams (if any).

        
        **Parameters:**

        * stream: the stdout/stderr stream;
        * isError: whether the building process generated an error or not;
        * processEnded: whether the process has just ended.
        """

        written, copy = False, True
        
        if stream.CanRead():
            # There is some data, process it
            text = stream.read()
            if isError and text.strip():
                # Ah, is the error stream, something went wrong
                self.MainFrame.SendMessage(2, text)
                self.failed = True
                self.fullText = ""
                self.outputText += text
            else:
                # That's the input stream
                if text.find("byte-compiling") >= 0:    # py2exe/py2app is compiling
                    self.MainFrame.SendMessage(4, _("Byte-compiling Python files..."), True)
                elif text.find("copying") >= 0:         # py2exe is copying files
                    self.MainFrame.SendMessage(5, _("Copying files..."), True)
                elif text.find("searching") >= 0:       # py2exe is searching for modules
                    self.MainFrame.SendMessage(3, _("Finding required modules..."), True)
                elif text.find("skipping") >= 0:        # py2app skipping loaders
                    self.MainFrame.SendMessage(6, _("Skipping Python loaders/byte-compilation..."), True)
                elif text.find("filtering") >= 0:       # py2app filtering dependencies
                    self.MainFrame.SendMessage(7, _("Filtering Dependencies..."), True)
                else:
                    copy = False

                # Store the text from the input stream
                self.fullText += text
                self.outputText += text
                written = True
                
        if not isError:
            if self.compiler in ["bbfreeze", "PyInstaller"]:
                # bbFreeze and PyInstaller do not give intelligent
                # messages in the stdout
                self.MainFrame.SendMessage(4, _("Running compilation steps..."))
            elif not written:
                if copy:
                    self.MainFrame.CopyLastMessage()
                else:
                    self.MainFrame.SendMessage(4, _("Running compilation steps..."), True)
        

    def ProcessOutputText(self):
        """ Process the result of the compilation steps. """

        self.project.hasBeenCompiled = True
        
        if self.compiler != "py2exe":
            # This is available only for py2exe
            return
        
        # Look for what py2exe thinks are the missing modules
        indx = self.fullText.rfind("The following modules")
        moduleText = self.fullText[indx:]
        # They are usually put inside square braces
        indx1, indx2 = moduleText.find("["), moduleText.find("]")
        if indx1 < 0 or indx2 < 0:
            missingModules = []
        else:
            missingModules = eval(moduleText[indx1:indx2+1])
            missingModules = [tuple(miss.split(".")) for miss in missingModules]

        # Look for what py2exe thinks are the binary dependencies
        binaryDependencies = []
        text = self.fullText
        indx = text.find("*** binary dependencies ***")
        text = text[indx:].split("\n")
        text = text[7:]
        # Here it's bit tricky, but it works
        for line in text:
            line = line.strip().split("-")
            dll, path = line[0], "".join(line[1:])
            if not dll:
                break
            binaryDependencies.append([dll.strip(), opj(path.strip())])

        self.project.SetCompilationData(missingModules, binaryDependencies)


