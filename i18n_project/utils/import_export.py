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

TAG_SPLIT_RE = re.compile(r'[^a-zA-Z]+')

def extract_phrase_source(prj,unit):
    slang = unit.getsourcelanguage() or 'en'
    phrase_options = extract_formats(unit)
    phrase_tags = []
    if unit.getcontext():
        phrase_tags = TAG_SPLIT_RE.split(unit.getcontext())
    tags = [t for t in phrase_tags if t]

    if prj.identity_method == 'orig':
        message_options = {}
        msgid = extract_message(unit.getsource(),phrase_options,message_options)
        p = prj.get_phrase(msgid,tags)
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
        p = prj.get_phrase(msgid,tags)
        if not p:
            identity = dict(int_identity=int(msgid)) if prj.identity_method == 'int' else dict(enum_identity=msgid)
            p = prj.phrases.create(options=phrase_options,**identity)
        else:
            p.options = phrase_options
    p.save()
    p.tags.clear()
    p.tags.add(*tags)
    if unit.hasplural():
        if prj.identity_method == 'orig':
            p.orig_identity.mode_id = 0
            p.orig_identity.save()
            t,tc = p.translations.get_or_create(language=slang,mode_id=1)
            t.mode_id = 1
            t.language = slang
            t.original=unit.getsource().strings[1]
            t.save()
    return p

def extract_phrase_target(phrase,unit,lang,headerplural):
    tlang = lang # not valid in common case! or unit.gettargetlanguage()
    prj = phrase.project

    if unit.hasplural():
        targets = unit.gettarget().strings
        for mode_id in range(len(targets)):
            t,tc = phrase.translations.get_or_create(language=tlang,mode_id=mode_id)
            t.mode_id = mode_id
            t.language = tlang
            t.options = {}
            t.options['mode_formula'] = headerplural
            if targets[mode_id]:
                t.original = targets[mode_id]
            else:
                if len(unit.getsource().strings) > mode_id:
                    t.original = unit.getsource().strings[mode_id]
                    t.options['source'] = True
                else:
                    t.original = unit.getsource().strings[-1]
                    t.options['source'] = True
            t.save()
    else:
        t,tc = phrase.translations.get_or_create(language=tlang)
        t.mode_id = None
        t.language = tlang
        t.options = {}
        t.original=unit.gettarget()
        if unit.gettarget():
            t.original=unit.gettarget()
        else:
            t.original = unit.getsource()
            t.options['source'] = True
        t.save()
    return phrase

def extract_phrase(prj,unit,lang,headerplural):
    p = extract_phrase_source(prj,unit)
    extract_phrase_target(p,unit,lang,headerplural)
    return p

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
        extract_phrase(prj,unit,lang,f.getheaderplural()[1])
