# -*- coding: utf-8 -*-
#####################################################################
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2009 Pascal Giard                                   #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License       #
# as published by the Free Software Foundation; either version 2    #
# of the License, or (at your option) any later version.            #
#                                                                   #
# This program is distributed in the hope that it will be useful,   #
# but WITHOUT ANY WARRANTY; without even the implied warranty of    #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
# GNU General Public License for more details.                      #
#                                                                   #
# You should have received a copy of the GNU General Public License #
# along with this program; if not, write to the Free Software       #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,        #
# MA  02110-1301, USA.                                              #
#####################################################################

'''
Misc util functions and things that augment functions in Python and base libs.

Created on Oct 23, 2017

@author: wrzwicky
'''

import glob, os

def globfile(dir, pattern="*"):
    """
    Match the files in a single dir.
    Work around for glob and fnmatch not having a way to escape characters
    such as [ ] in filepaths.
    Like glob, if dir does not exists, then returns empty list.
    """
    # work around for glob and fnmatch not having a way to escape characters
    # such as [ ] in filepaths... wtf glob! Python 3.3 added glob.escape to
    # escape all characters that cause the problem. For now the change dir
    # method is a cleaner work around than reimplementing that function here.
    if os.path.exists(dir):
        origpath = os.path.abspath('.')
        os.chdir(dir)
        files = glob.glob(pattern)
        os.chdir(origpath)
        return [os.path.join(dir,f) for f in files]
    else:
        return []

#Alternative glob() that escapes [ ].
#    # glob parses [] but those are legal chars on Windows, so we must escape them.
#    # it must be done like this so replacements are not mangled by other replacements.
#    replacements = {
#        "[": "[[]",
#        "]": "[]]"
#    }
#    fileName1 = "".join([replacements.get(c,c) for c in fileName1])
#    files = glob.glob('%s.*' % fileName1)
