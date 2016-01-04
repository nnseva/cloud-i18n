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

def extract_message(msg,options):
    f = options.get('format',None)
    if not f:
        return msg
    if msg:
        options['prefix'],msg,options['suffix'] = STRIP_RE.match(msg).groups()
    else:
        options['prefix'],msg,options['suffix'] = '','',''
    options['formats'] = options.get('formats',{})
    pattern = '[##]'
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
    if reps:
        options['formats'][f]['replacements'] = reps
    else:
        del options['format']
        del options['formats']
    return msg

def extract_formats(unit,options=None):
    if not options:
        options = {}
    for f in FORMATS:
        if unit.hastypecomment(f):
            options['format'] = f
    return options

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
        options = extract_formats(unit)

        if prj.identity_method == 'orig':
            msgid = extract_message(unit.getsource(),options)
            p = prj.get_phrase(msgid)
            if not p:
                p = prj.phrases.create()
                t = p.translations.create(original=unit.getsource(),language=slang,options=options)
                p.orig_identity = t
                p.save()
            else:
                t = p.translations.get(message=msgid,language=slang)
                t.original = unit.getsource()
                t.options = options
                t.save()
        else:
            msgid=unit.getsource()
            p = prj.get_phrase(msgid)
            if not p:
                identity = dict(int_identity=int(msgid)) if prj.identity_method == 'int' else dict(enum_identity=msgid)
                p = prj.phrases.create(**identity)

        if unit.hasplural():
            if prj.identity_method == 'orig':
                p.orig_identity.mode_id = 0
                p.orig_identity.save()
                t,tc = p.translations.get_or_create(language=slang,mode_id=1)
                t.options = options
                t.mode_id = 1
                t.language = slang
                t.original=unit.getsource().strings[1]
                t.save()
            targets = unit.gettarget().strings
            for mode_id in range(len(targets)):
                t,tc = p.translations.get_or_create(language=tlang,mode_id=mode_id)
                t.options = options
                t.mode_id = mode_id
                t.language = tlang
                t.options['mode_formula'] = f.getheaderplural()[1]
                t.original = targets[mode_id]
                if unit.isfuzzy():
                    t.options['fuzzy'] = True
                t.save()
        else:
            t,tc = p.translations.get_or_create(language=tlang)
            t.options = options
            t.original=unit.gettarget()
            t.mode_id = None
            t.language = tlang
            if unit.isfuzzy():
                t.options['fuzzy'] = True
            t.save()
        #print ">>>",unit.isfuzzy(),options.get('fuzzy','NOP'),unit.getsource()
