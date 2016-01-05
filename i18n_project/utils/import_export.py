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

def extract_message(msg,phrase_options,message_options):
    f = phrase_options.get('format',None)
    if not f:
        return msg
    if msg:
        message_options['prefix'],msg,message_options['suffix'] = STRIP_RE.match(msg).groups()
    else:
        message_options['prefix'],msg,message_options['suffix'] = '','',''
    message_options['formats'] = {}
    pattern = '[##]'
    message_options['formats'][f] = {}
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
        message_options['formats'][f]['replacements'] = reps
    else:
        del message_options['formats']
    return msg

def extract_formats(unit,options=None):
    if not options:
        options = {}
    for f in FORMATS:
        if unit.hastypecomment(f):
            options['format'] = f
    options['fuzzy'] = bool(unit.isfuzzy())
    if not options['fuzzy']:
        del options['fuzzy']
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
        phrase_options = extract_formats(unit)

        if prj.identity_method == 'orig':
            message_options = {}
            msgid = extract_message(unit.getsource(),phrase_options,message_options)
            p = prj.get_phrase(msgid)
            if not p:
                p = prj.phrases.create(options=phrase_options)
                t = p.translations.create(original=unit.getsource(),language=slang)
                p.orig_identity = t
            else:
                p.options = phrase_options
                t = p.translations.get(message=msgid,language=slang)
                t.original = unit.getsource()
                t.save()
        else:
            msgid=unit.getsource()
            p = prj.get_phrase(msgid)
            if not p:
                identity = dict(int_identity=int(msgid)) if prj.identity_method == 'int' else dict(enum_identity=msgid)
                p = prj.phrases.create(options=phrase_options,**identity)
            else:
                p.options = phrase_options
        p.save()
        if unit.hasplural():
            if prj.identity_method == 'orig':
                p.orig_identity.mode_id = 0
                p.orig_identity.save()
                t,tc = p.translations.get_or_create(language=slang,mode_id=1)
                t.mode_id = 1
                t.language = slang
                t.original=unit.getsource().strings[1]
                t.save()
            targets = unit.gettarget().strings
            for mode_id in range(len(targets)):
                t,tc = p.translations.get_or_create(language=tlang,mode_id=mode_id)
                t.mode_id = mode_id
                t.language = tlang
                t.original = targets[mode_id]
                t.options = {}
                t.options['mode_formula'] = f.getheaderplural()[1]
                t.save()
        else:
            t,tc = p.translations.get_or_create(language=tlang)
            t.original=unit.gettarget()
            t.mode_id = None
            t.language = tlang
            t.save()
        #print ">>>",unit.isfuzzy(),options.get('fuzzy','NOP'),unit.getsource()
