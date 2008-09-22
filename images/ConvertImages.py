import glob
import os
from wx.tools import img2py

_imgExtensions = ["*.ico", "*.jpeg", "*.jpg", "*.gif", "*.xpm", "*.bmp", "*.png"]

files = []
for imgType in _imgExtensions:
    files += glob.glob(imgType)

for python_file in ["../AllIcons.py", "../AllIcons.pyo", "../AllIcons.pyc"]:
    if os.path.isfile(python_file):
        os.remove(python_file)

python_file = "../AllIcons.py"

for fileName in files:
    append = True
    if not os.path.isfile(python_file):
        append = False
        
    img2py.img2py(fileName, python_file, append=append, compressed=False, catalog=True)

    


    