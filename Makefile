#
# Makefile for vfatqc package
#

BUILD_HOME := $(shell dirname `pwd`)

Project      := vfatqc-python-scripts
ShortProject := vfatqc
Namespace    := gempython
Package      := vfatqc-python-scripts
ShortPackage := vfatqc
LongPackage  := vfatqc
PackageName  := $(Namespace)_$(ShortPackage)
PackageDir   := pkg/$(Namespace)/$(ShortPackage)
# PackageDir   := pkg/vfatqc_python_scripts


# Explicitly define the modules that are being exported (for PEP420 compliance)
PythonModules = ["$(Namespace).$(ShortPackage)"]
$(info PythonModules=${PythonModules})

VFATQC_VER_MAJOR=0
VFATQC_VER_MINOR=3
VFATQC_VER_PATCH=1

include $(BUILD_HOME)/$(Project)/config/mfCommonDefs.mk
include $(BUILD_HOME)/$(Project)/config/mfPythonDefs.mk

# include $(BUILD_HOME)/$(Project)/config/mfDefs.mk

include $(BUILD_HOME)/$(Project)/config/mfPythonRPM.mk

default:
	@echo "Running default target"
	$(MakeDir) $(PackageDir)
	@echo "__path__ = __import__('pkgutil').extend_path(__path__, __name__)" > pkg/$(Namespace)/__init__.py
	@cp -rfp __init__.py $(PackageDir)

# need to ensure that the python only stuff is packaged into RPMs
.PHONY: clean preprpm
_rpmprep: preprpm
	@echo "Running _rpmprep target"
preprpm: default
	@echo "Running preprpm target"
	@cp -rfp requirements.txt README.md CHANGELOG.md LICENSE $(PackageDir)
	@cp -rfp requirements.txt README.md CHANGELOG.md pkg
	$(MakeDir) $(PackageDir)/bin
	@cp -rfp run_scans.py   $(PackageDir)/bin
	@cp -rfp trimChamber.py $(PackageDir)/bin
	@cp -rfp fastLatency.py $(PackageDir)/bin
	@cp -rfp ultra*.py      $(PackageDir)/bin
	@cp -rfp conf*.py       $(PackageDir)/bin

clean:
	@echo "Running clean target"
	@rm -rf $(PackageDir)/bin
	@rm -f  $(PackageDir)/LICENSE
	@rm -f  $(PackageDir)/MANIFEST.in
	@rm -f  $(PackageDir)/requirements.txt
	@rm -f  $(PackageDir)/README.md
	@rm -f  $(PackageDir)/CHANGELOG.md
	@rm -f  $(PackageDir)/__init__.py
	@rm -f  pkg/$(Namespace)/__init__.py
	@rm -f  pkg/README.md
	@rm -f  pkg/CHANGELOG.md
	@rm -f  pkg/requirements.txt

print-env:
	@echo BUILD_HOME     $(BUILD_HOME)
	@echo GIT_VERSION    $(GIT_VERSION)
	@echo PYTHON_VERSION $(PYTHON_VERSION)
	@echo GEMDEVELOPER   $(GEMDEVELOPER)
