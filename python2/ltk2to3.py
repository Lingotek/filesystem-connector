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

dir2 = 'python2/ltk'
files2 = get_files(dir2)

# Copy files from 2 to 3
for fpath2 in files2:
    fpath3 = fpath2.replace('python2','python3')
    shutil.copyfile(fpath2, fpath3)

# Comment and uncomment specified lines in Python 3 version
for fpath in files2:
    fpath = fpath.replace('python2','python3')
    with open(fpath, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate()
        is_python3 = False
        is_python2 = False
        for line in lines:
            if '# Python 3' in line:
                is_python3 = True
            elif is_python3:
                if '# End Python 3' in line:
                    is_python3 = False
                    continue
                line = line.replace('# ','')
            elif '# Python 2' in line:
                is_python2 = True
            elif is_python2:
                if '# End Python 2' in line:
                    is_python2 = False
                    continue
                line = '# '+str(line)
            f.write(line)