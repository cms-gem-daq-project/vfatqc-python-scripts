#!/bin/sh

# default action
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

# install 'scripts' to /opt/cmsgemos/bin
mkdir -p %{buildroot}/opt/cmsgemos/bin
cp -rfp gempython/scripts/*.py %{buildroot}/opt/cmsgemos/bin/

cp INSTALLED_FILES INSTALLED_FILES.bac
# cat INSTALLED_FILES.bac \
#     | egrep -v 'gempython/scripts|/usr/gempython' > INSTALLED_FILES
# cat INSTALLED_FILES.bac \
#     | fgrep 'gempython/scripts' \
#     | egrep -v 'pyc|pyo|/usr/gempython' >> INSTALLED_FILES
# cat INSTALLED_FILES.bac \
#     | fgrep '/opt/cmsgmos/bin' \
#     | egrep -v 'pyc|pyo' >> INSTALLED_FILES
rm INSTALLED_FILES.bac

# set permissions
cat <<EOF >>INSTALLED_FILES
%attr(-,root,root) /opt/cmsgemos/bin/*.py
EOF
echo "Modified INSTALLED_FILES"
cat INSTALLED_FILES
