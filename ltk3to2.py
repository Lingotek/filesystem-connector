import os
import shutil
import fnmatch

def get_files(patterns):
    """ gets all files matching pattern from root
        pattern supports any unix shell-style wildcards (not same as RE) """

    cwd = os.getcwd()
    if isinstance(patterns,str):
        patterns = [patterns]

    matched_files = []
    for pattern in patterns:
        path = os.path.abspath(pattern)
        # print("looking at path "+str(path))
        # check if pattern contains subdirectory
        if os.path.exists(path):
            if os.path.isdir(path):
                for root, subdirs, files in os.walk(path):
                    split_path = root.split('/')
                    for file in files:
                        # print(os.path.join(root, file))
                        if fnmatch.fnmatch(file, '*.py'):
                            matched_files.append(os.path.join(root, file))
            else:
                matched_files.append(path)
        else:
            logger.info("File not found: "+pattern)
    if len(matched_files) == 0:
        return None
    return matched_files

dir3 = 'python3/ltk'
files3 = get_files(dir3)

# Copy files from 3 to 2
for fpath3 in files3:
    fpath2 = fpath3.replace('python3','python2')
    shutil.copyfile(fpath3, fpath2)

# Comment and uncomment specified lines in Python 2 version
for fpath in files3:
    fpath = fpath.replace('python3','python2')
    with open(fpath, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate()
        is_python2 = False
        is_python3 = False
        for line in lines:
            if '# Python 2' in line:
                is_python2 = True
            elif is_python2:
                if '# End Python 2' in line:
                    is_python2 = False
                    continue
                line = line.replace('# ','')
            elif '# Python 3' in line:
                is_python3 = True
            elif is_python3:
                if '# End Python 3' in line:
                    is_python3 = False
                    continue
                line = '# '+str(line)
            f.write(line)