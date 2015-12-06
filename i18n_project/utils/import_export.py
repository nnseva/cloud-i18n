import logging

from translate.storage.factory import getclass

logger = logging.getLogger(__name__)

import re

STRIP_RE = re.compile(r'^([ \r\n\t]*)([^ \r\n\t]?(?:.|\n|\r)*[^ \r\n\t])([ \r\n\t]*)$')
FORMATS = {
    'python-format':re.compile(r'%(\([^)]*\))?([-+#0 ]*)?(([0-9]+)|(\*))?(\.(([0-9]+)|(\*)))?([hlL])?([diouxXeEfFgGcrs])'),
    'python-brace-format':re.compile(r'\{([a-zA-Z0-9_][a-zA-Z0-9_.\[\]]*)?(![rs])?(:.?[><=^]?[-+ ]?#?0?([0-9]+)?,?(\.[0-9]+)?[bcdeEfFgGnosxX%]?)?\}'),
    # TODO: ALL OTHER FORMATS
}

def normalize_message(unit,msg,options):
    if not msg:
        return msg
    options['prefix'],msg,options['suffix'] = STRIP_RE.match(msg).groups()
    options['formats'] = options.get('formats',{})
    pattern = '[##]'
    for f in FORMATS:
        if unit.hastypecomment(f):
            options['format'] = f
            options['formats'][f] = options['formats'].get(f,{})
            start = 0
            reps = []
            while 42:
                m = FORMATS[f].search(msg,start)
                if not m:
                    break
                rep = m.group(0)
                msg = msg[:m.start()]+pattern+msg[m.end():]
                reps.append({
                    'start':m.start(),
                    'stop':m.start()+len(pattern),
                    'local':rep,
                })
                start = m.start()+len(pattern)
            options['formats'][f]['replacements'] = reps
    return msg

def import_file(file, prj, lang=None):
    f = getclass(file)(file.read())
    if not hasattr(f, "parseheader"):
        raise Exception("Format is not supported")

    header = f.parseheader()
    if not lang:
        lang = header['Language']
    if not lang:
        raise Exception("Language not set")
    for unit in f.getunits():
        tlang = unit.gettargetlanguage() or lang
        slang = unit.getsourcelanguage() or 'en'
        if prj.identity_method == 'orig':
            options = {}
            msgid = normalize_message(unit,unit.getsource(),options)
            p,pc = prj.get_or_create_phrase(msgid,slang)
            if pc:
                p.orig_identity.options = options
                p.orig_identity.save()
        else:
            msgid=unit.getsource()
            p,pc = prj.get_or_create_phrase(msgid,slang)
        if unit.hasplural():
            if prj.identity_method == 'orig':
                p.orig_identity.mode_id = 0
                p.orig_identity.save()
                t,tc = p.translations.get_or_create(language=slang,mode_id=1)
                if not t.options: t.options = {}
                t.message=normalize_message(unit,unit.getsource().strings[1],t.options)
                t.mode_id = 1
                t.language = slang
                t.save()
            targets = unit.gettarget().strings
            for mode_id in range(len(targets)):
                t,tc = p.translations.get_or_create(language=tlang,mode_id=mode_id)
                if not t.options: t.options = {}
                t.message = normalize_message(unit,targets[mode_id],t.options)
                t.mode_id = mode_id
                t.language = tlang
                t.options['mode_formula'] = f.getheaderplural()[1]
                if unit.isfuzzy():
                    t.options['fuzzy'] = True
                t.save()
        else:
            t,tc = p.translations.get_or_create(language=tlang)
            if not t.options: t.options = {}
            t.message=normalize_message(unit,unit.gettarget(),t.options)
            t.mode_id = None
            t.language = tlang
            if unit.isfuzzy():
                t.options['fuzzy'] = True
            t.save()
