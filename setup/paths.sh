# Setup cmsgemos
echo "Checking paths" 

#export BUILD_HOME=<your path>/cmsgemos/../
if [[ -n "$BUILD_HOME" ]]; then
    echo BUILD_HOME $BUILD_HOME
else
    echo "BUILD_HOME not set, please set BUILD_HOME to the directory above the root of your repository"
    echo " (export BUILD_HOME=<your path>/cmsgemos/../) and then rerun this script"
    return
fi

#export DATA_PATH=/<your>/<data>/<directory>
if [[ -n "$DATA_PATH" ]]; then
    echo DATA_PATH $DATA_PATH
else
    echo "DATA_PATH not set, please set DATA_PATH to a directory where data files created by scan applications will be written"
    echo " (export DATA_PATH=<your>/<data>/<directory>/) and then rerun this script"
    return
fi

# Checking GEM_PYTHON_PATH
if [[ -n "$GEM_PYTHON_PATH" ]]; then
    echo GEM_PYTHON_PATH $GEM_PYTHON_PATH
else
    echo "GEM_PYTHON_PATH not set, please source \$BUILD_HOME/cmsgemos/setup/paths.sh"
    return
fi

# Checking GEM_PLOTTING_PROJECT
if [[ -n "$GEM_PLOTTING_PROJECT" ]]; then
    echo GEM_PLOTTING_PROJECT $GEM_PLOTTING_PROJECT
else
    echo "GEM_PLOTTING_PROJECT not set, please source \$BUILD_HOME/gem-plotting-tools/setup/paths.sh"
fi

# Adding Scan Applications to Path
export "PATH=$PATH:$BUILD_HOME/vfatqc-python-scripts"
export "PYTHONPATH=$PYTHONPATH:$BUILD_HOME/vfatqc-python-scripts"

# Done
echo "Setup Complete"
