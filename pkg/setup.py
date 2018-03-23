
from setuptools import setup,find_packages

from os import listdir
from os.path import isfile,join
scriptdir  = 'gempython/vfatqc/bin'
scriptpath = '/opt/cmsgemos/bin'
scripts    = listdir(scriptdir)

def readme():
    with open('README.md') as f:
        return f.read()

def getscripts():
    # would prefer to use this for executables, if one can control the install location
    # to be user defined rather than /usr/bin
    # return dict(('{0:s}/{1:s}'.format(scriptpath,x),
    #       '{0:s}/{1:s}'.format(scriptdir,x)) for x in scripts if isfile(join(scriptdir,x)) )
    return ['{0:s}/{1:s}'.format(scriptdir,x) for x in scripts if isfile(join(scriptdir,x)) ]

def getpkgdata():
    # actual package data
    data = dict((pkg,['*.txt','*.so']) for pkg in __pythonmodules__)
    # hack just to get the build to work
    data['gempython/bin'] = ['gempython/vfatqc/bin/*.py']
    return data

def getreqs():
    with open('gempython/vfatqc/requirements.txt') as f:
        reqs = f.readlines()
        return [x.strip() for x in reqs]

setup(name             = '__packagename__',
      version          = '__version__',
      # use_scm_version  = True,
      description      = '__description__',
      long_description = readme(),
      # author           = __author__,
      author           = 'GEM Online Systems Group',
      # author_email     = __author_email__,
      author_email     = 'cms-gem-online-sw@cern.ch',
      # url              = __url__,
      url              = 'https://cms-gem-daq-project.github.io/vfatqc-python-tools',
      install_requires = getreqs(),
      # install_requires = ['numpy>=1.7'],
      # scripts          = getscripts(),
      # build_requires   = '__build_requires__',
      # namespace_package = "gempython",
      # packages         = __pythonmodules__, # for PEP420 native namespace util
      packages           = find_packages(), # for pkgutil namespace method
      # package_dir      = {'' : ''},
      package_data     = getpkgdata(),
      # dependency_links   = ['http://cmsgemos.web.cern.ch/cmsgemos/repo/tarball/master#egg=package-1.0']
      zip_safe         = False,
      data_files       = [('/opt/cmsgemos/bin', ['{0:s}/{1:s}'.format(scriptdir,x) for x in scripts if isfile(join(scriptdir,x))])],
      build_requires   = ['importlib; python_version=="2.6"','setuptools>=25.0','setuptools_scm'],
      setup_requires   = ['importlib; python_version=="2.6"','setuptools>=25.0'],
      license          = 'MIT',
)
