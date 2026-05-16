# Resource object code (Python 3)
# Created by: object code
# Created by: The Resource Compiler for Qt version 6.11.1
# WARNING! All changes made in this file will be lost!

from PySide6 import QtCore

qt_resource_data = b"\
\x00\x00\x01\x9e\
/\
* Feuille embarq\
u\xc3\xa9e (qrc) pour \
valider les asse\
ts packag\xc3\xa9s */\x0a\
body {\x0a  font-fa\
mily: system-ui,\
 sans-serif;\x0a  m\
argin: 2rem;\x0a  b\
ackground: #fff8\
f0;\x0a  color: #2e\
1a1a;\x0a}\x0a\x0a.meta {\
\x0a  color: #664;\x0a\
}\x0a\x0a#status {\x0a  f\
ont-weight: 600;\
\x0a}\x0a\x0a.ok {\x0a  colo\
r: #9a4d0a;\x0a}\x0a\x0a#\
log {\x0a  backgrou\
nd: #fff;\x0a  bord\
er: 1px solid #d\
db;\x0a  padding: 0\
.75rem;\x0a  min-he\
ight: 4rem;\x0a}\x0a\x0ab\
utton {\x0a  margin\
: 0.5rem 0 1rem;\
\x0a  padding: 0.4r\
em 0.9rem;\x0a}\x0a\
\x00\x00\x07\x85\
/\
* Pont QWebChann\
el minimal \xe2\x80\x94 s\
pike PLO-44 (mod\
e qrc:). */\x0a\x0a(fu\
nction () {\x0a  co\
nst statusEl = d\
ocument.getEleme\
ntById(\x22status\x22)\
;\x0a  const cssEl \
= document.getEl\
ementById(\x22css-c\
heck\x22);\x0a  const \
logEl = document\
.getElementById(\
\x22log\x22);\x0a  const \
btn = document.g\
etElementById(\x22b\
tn-ping\x22);\x0a\x0a  fu\
nction log(line)\
 {\x0a    logEl.tex\
tContent += line\
 + \x22\x5cn\x22;\x0a  }\x0a\x0a  \
/** Qt 6 WebChan\
nel renvoie souv\
ent une Promise \
pour les @Slot a\
vec result. */\x0a \
 function qtInvo\
ke(callable) {\x0a \
   const value =\
 callable();\x0a   \
 if (value && ty\
peof value.then \
=== \x22function\x22) \
{\x0a      return v\
alue;\x0a    }\x0a    \
return Promise.r\
esolve(value);\x0a \
 }\x0a\x0a  const cssO\
k = getComputedS\
tyle(document.bo\
dy).backgroundCo\
lor !== \x22rgba(0,\
 0, 0, 0)\x22;\x0a  cs\
sEl.textContent \
= cssOk\x0a    ? \x22C\
SS embarqu\xc3\xa9 : c\
harg\xc3\xa9 (fond tei\
nt\xc3\xa9)\x22\x0a    : \x22CS\
S embarqu\xc3\xa9 : no\
n d\xc3\xa9tect\xc3\xa9\x22;\x0a  \
cssEl.classList.\
toggle(\x22ok\x22, css\
Ok);\x0a\x0a  if (type\
of qt === \x22undef\
ined\x22) {\x0a    sta\
tusEl.textConten\
t = \x22Qt WebChann\
el indisponible \
(qt manquant).\x22;\
\x0a    return;\x0a  }\
\x0a\x0a  new QWebChan\
nel(qt.webChanne\
lTransport, func\
tion (channel) {\
\x0a    const bridg\
e = channel.obje\
cts.bridge;\x0a    \
if (!bridge) {\x0a \
     statusEl.te\
xtContent = \x22Obj\
et \xc2\xab bridge \xc2\xbb \
absent du QWebCh\
annel.\x22;\x0a      r\
eturn;\x0a    }\x0a\x0a  \
  if (bridge.log\
FromJs && bridge\
.logFromJs.conne\
ct) {\x0a      brid\
ge.logFromJs.con\
nect(function (m\
sg) {\x0a        lo\
g(\x22\xe2\x86\x90 JS \xc3\xa9mis \
: \x22 + msg);\x0a    \
  });\x0a    }\x0a\x0a   \
 qtInvoke(functi\
on () {\x0a      re\
turn bridge.load\
erLabel ? bridge\
.loaderLabel() :\
 \x22?\x22;\x0a    }).the\
n(function (labe\
l) {\x0a      statu\
sEl.textContent \
= \x22Pont actif \xe2\x80\
\x94 mode \x22 + label\
;\x0a    });\x0a\x0a    b\
tn.addEventListe\
ner(\x22click\x22, fun\
ction () {\x0a     \
 qtInvoke(functi\
on () {\x0a        \
return bridge.pi\
ng(\x22bonjour depu\
is le spike\x22);\x0a \
     }).then(fun\
ction (reply) {\x0a\
        log(\x22\xe2\x86\x92\
 ping : \x22 + repl\
y);\x0a      });\x0a  \
  });\x0a\x0a    qtInv\
oke(function () \
{\x0a      return b\
ridge.ping(\x22d\xc3\xa9m\
arrage\x22);\x0a    })\
.then(function (\
reply) {\x0a      l\
og(\x22\xe2\x86\x92 ping aut\
o : \x22 + reply);\x0a\
    });\x0a  });\x0a})\
();\x0a\
\x00\x00\x02\xf9\
<\
!DOCTYPE html>\x0a<\
html lang=\x22fr\x22>\x0a\
  <head>\x0a    <me\
ta charset=\x22utf-\
8\x22 />\x0a    <meta \
name=\x22viewport\x22 \
content=\x22width=d\
evice-width, ini\
tial-scale=1\x22 />\
\x0a    <title>Spik\
e WebEngine \xe2\x80\x94 \
qrc:</title>\x0a   \
 <link rel=\x22styl\
esheet\x22 href=\x22st\
yle.css\x22 />\x0a  </\
head>\x0a  <body da\
ta-loader=\x22qrc\x22>\
\x0a    <main>\x0a    \
  <h1>Markdown C\
onverter \xe2\x80\x94 spi\
ke WebEngine</h1\
>\x0a      <p class\
=\x22meta\x22>Chargeme\
nt <strong>qrc:<\
/strong> (ressou\
rces embarqu\xc3\xa9es\
 Qt)</p>\x0a      <\
p id=\x22status\x22>In\
itialisation du \
pont\xe2\x80\xa6</p>\x0a    \
  <p id=\x22css-che\
ck\x22 class=\x22ok\x22>C\
SS embarqu\xc3\xa9 : e\
n attente</p>\x0a  \
    <button type\
=\x22button\x22 id=\x22bt\
n-ping\x22>Ping Pyt\
hon</button>\x0a   \
   <pre id=\x22log\x22\
></pre>\x0a    </ma\
in>\x0a    <script \
src=\x22qrc:///qtwe\
bchannel/qwebcha\
nnel.js\x22></scrip\
t>\x0a    <script s\
rc=\x22app.js\x22></sc\
ript>\x0a  </body>\x0a\
</html>\x0a\
"

qt_resource_name = b"\
\x00\x05\
\x00zp\x15\
\x00s\
\x00p\x00i\x00k\x00e\
\x00\x09\
\x00(\xbf#\
\x00s\
\x00t\x00y\x00l\x00e\x00.\x00c\x00s\x00s\
\x00\x06\
\x06\x875\x13\
\x00a\
\x00p\x00p\x00.\x00j\x00s\
\x00\x0a\
\x0c\xba\xf2|\
\x00i\
\x00n\x00d\x00e\x00x\x00.\x00h\x00t\x00m\x00l\
"

qt_resource_struct = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x10\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
\x00\x00\x01\x9e,B:\xc2\
\x00\x00\x00(\x00\x00\x00\x00\x00\x01\x00\x00\x01\xa2\
\x00\x00\x01\x9e,Y\xbav\
\x00\x00\x00:\x00\x00\x00\x00\x00\x01\x00\x00\x09+\
\x00\x00\x01\x9e,B:\xb5\
"


def qInitResources():
    QtCore.qRegisterResourceData(0x03, qt_resource_struct, qt_resource_name, qt_resource_data)


def qCleanupResources():
    QtCore.qUnregisterResourceData(0x03, qt_resource_struct, qt_resource_name, qt_resource_data)


qInitResources()
