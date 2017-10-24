#!/usr/local/bin/python2.7
# encoding: utf-8
'''
make_career -- build a career.ini file for fofix

@author:     William R. Zwicky

@copyright:  2017 fofix. All rights reserved.

@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

import random
import string
import sys
import os
import json
import hashlib
from ConfigParser import *
from collections import OrderedDict


## ----------------------------------------------------- ##

#https://stackoverflow.com/a/32888599
class CaseInsensitiveDict(OrderedDict):
    @classmethod
    def _k(cls, key):
        return key.lower() if isinstance(key, basestring) else key

    def __init__(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        self._convert_keys()
    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(self.__class__._k(key))
    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(self.__class__._k(key), value)
    def __delitem__(self, key):
        return super(CaseInsensitiveDict, self).__delitem__(self.__class__._k(key))
    def __contains__(self, key):
        return super(CaseInsensitiveDict, self).__contains__(self.__class__._k(key))
    def has_key(self, key):
        return super(CaseInsensitiveDict, self).has_key(self.__class__._k(key))
    def pop(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).pop(self.__class__._k(key), *args, **kwargs)
    def get(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).get(self.__class__._k(key), *args, **kwargs)
    def setdefault(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).setdefault(self.__class__._k(key), *args, **kwargs)
    def update(self, E={}, **F):
        super(CaseInsensitiveDict, self).update(self.__class__(E))
        super(CaseInsensitiveDict, self).update(self.__class__(**F))
    def _convert_keys(self):
        for k in list(self.keys()):
            v = super(CaseInsensitiveDict, self).pop(k)
            self.__setitem__(k, v)


## ----------------------------------------------------- ##


class Career:
    CAREER_FORMAT = "fofix-career-2"

    def __init__(self, name=None, subtitle=None):
        self.name = name
        self.subtitle = subtitle
        self.icon = None
        self.theme = None
        self.tiers = CaseInsensitiveDict() # maps tier.uid -> tier

    def toini(self, ini = None):
        if ini is None:
            ini = RawConfigParser(allow_no_value=True)

        ini.add_section('Career')

        if self.name:
            ini.set('Career', "Name:en-us", self.name)
        else:
            ini.set('Career', "#Name:en-us", '')

        if self.subtitle:
            ini.set('Career', "Subtitle:en-us", self.subtitle)
        else:
            ini.set('Career', "#Subtitle:en-us", '')

        ini.set('Career', 'format', Career.CAREER_FORMAT)

        if self.icon:
            ini.set('Career', "icon", self.icon)
        else:
            ini.set('Career', "#icon", '')

        if self.icon:
            ini.set('Career', "theme", self.theme)
        else:
            ini.set('Career', "#theme", '')

        if self.tiers:
            ini.set('Career', "Tiers", " ".join(t.uid for t in self.tiers.values()))
        else:
            ini.set('Career', "#Tiers", '')

        for t in self.tiers.values():
            t.toini(ini)

        return ini

    def tojson(self):
        """build a dict for use as json file"""
        d = OrderedDict()
        c = OrderedDict()
        c["career"] = d

        # (x or '') is an evil trick to convert None to empty string
        d["label"] = { "en-us" : (self.name or '') }
        d["subtitle"] = { "en-us" : (self.subtitle or '') }
        d["format"] = Career.CAREER_FORMAT
        d["icon"] = (self.icon or '')
        d["theme"] = (self.theme or '')
        d["tiers"] = []

        for k in sorted(self.tiers):
            t = self.tiers[k]
            d["tiers"].append(k)
            c[k] = t.tojson()

        return c

class Tier:
    def __init__(self, uid=None, name=None):
        self.uid = uid
        self.name = name
        self.unlock_require = None
        self.unlock_text = None
        self.songs = OrderedDict()
        self.warnings = []

    def toini(self, ini):
        ini.add_section(self.uid)

        if self.name:
            ini.set(self.uid, "Name:en-us", self.name)
        else:
            ini.set(self.uid, "#Name:en-us", '')

        if self.unlock_require:
            ini.set(self.uid, "unlock_require", self.unlock_require)
        else:
            ini.set(self.uid, "#unlock_require", '')

        if self.unlock_text:
            ini.set(self.uid, "unlock_text:en-us", self.unlock_text)
        else:
            ini.set(self.uid, "#unlock_text:en-us", '')

        for s in self.songs.values():
            ini.set(self.uid, 'Song_%s' % s.key, s.songhash+" #"+s.comment)

        for w in self.warnings:
            ini.set(self.uid, "# "+w)

    def tojson(self):
        d = OrderedDict()

        # (x or '') is an evil trick to convert None to empty string
        d["label"] = { "en-us" : (self.name or '') }
        d["unlock_require"] = (self.unlock_require or '')
        d["unlock_text"] = { "en-us" : (self.unlock_text or '') }

        # song.key is useless in json
        d["songs"] = ["%s #%s" % (s.songhash,s.comment) for s in self.songs.values()]
        if self.warnings:
            d["#warnings"] = self.warnings

        return d

class Song:
    key = None
    songhash = None
    comment = None


## ----------------------------------------------------- ##


def abbreviate(text):
    """ Keep only the first letter of each word. """
    text = text.lower()
    text = ''.join(c for c in text if c.isalpha() or c.isspace())
    text = "".join(word[0] for word in text.split())
    return text

def loadini(filepath):
    """ Load file into new ConfigParser. """
    ini = RawConfigParser()
    ini.read(filepath) #quietly skips if no file
    return ini


def iniget(ini, section, option, default):
    """ Getter for ConfigParser, but returns default value instead of exception. """
    try:
        return ini.get(section, option)
    except NoSectionError:
        return default
    except NoOptionError:
        return default


def import_titles(career, titles_ini):
    ''' Create tiers from titles.ini '''

    sections = iniget(titles_ini, 'titles', 'Sections', '')
    for section in sections.split():
        t = Tier()
        t.uid = iniget(titles_ini, section, 'Unlock_ID', section)
        t.name = iniget(titles_ini, section, 'Name', section)
        career.tiers[t.uid] = t


def import_songini(career, song_ini):
    ''' Update tier from song.ini '''

    tier_id = iniget(song_ini, 'song', 'Unlock_ID', None)
    unlock_require = iniget(song_ini, 'song', 'Unlock_Require', None)
    unlock_text = iniget(song_ini, 'song', 'Unlock_Text', None)

    if tier_id:
        try:
            t = career.tiers[tier_id]
        except KeyError:
            t = Tier(tier_id)
            career.tiers[tier_id] = t

        if not t.unlock_require:
            t.unlock_require = unlock_require
        elif t.unlock_require != unlock_require:
            t.warnings.append("also found unlock_require = %s" % unlock_require)

        if not t.unlock_text:
            t.unlock_text = unlock_text
        elif t.unlock_text != unlock_text:
            t.warnings.append("also found unlock_text = %s" % unlock_text)


## ----------------------------------------------------- ##


def loadFolder(topdir): # IGNORE:C0111
    """Scan a folder for titles.ini, song.ini, and metadata,
    and build a reasonable default career file."""

    def findfile(filelist, filename):
        # we are case insentive, but some OS are not, so this
        # checks if name in list insensitve, and return true name (with caps) if found
        filename = filename.lower()
        #if filename in map(str.lower, filelist):
        try:
            i = next(i for i,v in enumerate(filelist) if v.lower() == filename)
            return filelist[i]
        except StopIteration:
            return None

    try:
        # In case we need to generate tiers.
        tier_num = 900
        new_tier_map = {}
        # Help generate unique ini keys.
        keys = set()

        # Default career
        career = Career()
        career.name = os.path.basename(topdir)
        career.subtitle = "Generated by fofix.make_career"

        # Update with titles.ini if found
        f_titles = os.path.join(topdir, 'titles.ini')
        titles_ini = loadini(f_titles)
        import_titles(career, titles_ini)

        # Add all songs
        for dir,subdirs,files in os.walk(topdir):
            files.sort()

            # If it looks like a song, add it.
            f_notes = findfile(files, 'notes.mid')
            if not f_notes:
                #f_notes = findfile(files, 'notes.chart')
                try:
                    f_notes = next(f for f in files if f.lower().endswith(".chart"))
                except StopIteration:
                    # No *.chart file found; f_notes is already None
                    pass

            if f_notes:
                f_notes = os.path.join(dir, f_notes)

                # Hash the song chart
                songhash = hashlib.sha1(open(f_notes, 'rb').read()).hexdigest()

                nicename = dir
                tier_id = None

                # Get metadata
                f_ini = findfile(files, 'song.ini')
                if f_ini:
                    f_ini = os.path.join(dir, f_ini)

                    ini = loadini(f_ini)

                    name = iniget(ini, 'song', 'name', None)
                    artist = iniget(ini, 'song', 'artist', None)
                    tier_id = iniget(ini, 'song', 'unlock_id', None)

                    nicename = "%s - %s" % (artist, name)

                    import_songini(career, ini)

                # Find or create tier, as needed
                if tier_id:
                    try:
                        t = career.tiers[tier_id]
                    except KeyError:
                        t = Tier(tier_id)
                        t.warnings.append('Tier found in song.ini, missing from titles.ini' % (f_ini, f_titles))
                        career.tiers[tier_id] = t
                else:
                    # Make tier from parent dir.
                    # If songs are sorted into tier dirs, will be wonderful.
                    # If not, no harm done.
                    tier_name = os.path.basename(os.path.dirname(dir))
                    try:
                        tier_id = new_tier_map[tier_name]
                    except KeyError:
                        tier_id = "Tier_%s" % tier_num
                        new_tier_map[tier_name] = tier_id
                        tier_num += 1
                    try:
                        t = career.tiers[tier_id]
                    except KeyError:
                        t = Tier(tier_id, tier_name)
                        career.tiers[tier_id] = t

                # We need a unique key for ini file (always 6 chars so file has neat columns)
                #  - first try abbreviating nicename
                key = abbreviate(nicename)
                key = (key+"______")[:6]
                #  - if duplicate, replace with random chars
                while key in keys:
                    key = ''.join(random.choice(string.ascii_lowercase) for _ in range(6))
                keys.add(key)

                s = Song()
                s.key = key
                s.songhash = songhash
                s.comment = nicename
                t.songs[key] = s

        return career

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0


def main(argv=None): # IGNORE:C0111
    if len(argv) < 2:
        print("Tell me which folder!")
        sys.exit(5)

    topdir = os.path.abspath(argv[1])
    career = loadFolder(topdir)

#    outini = career.toini()
#    with open(os.path.join(topdir, '_generated_career_.ini'), 'wt') as fp:
#        outini.write(fp)

    outjson = career.tojson()
    fil = os.path.join(topdir, '_generated_career_.json')
    with open(fil, 'wt') as fp:
#        json.dumps(outjson).write(fp)
#        print json.dumps(outjson)
        json.dump(outjson, fp, indent=4)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
