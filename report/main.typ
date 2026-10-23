#import "template/layout.typ": writeup, appendix
#import "@preview/wordometer:0.1.6": word-count, total-words

#show: word-count.with(exclude: (figure, <no-wc>))

#show: writeup.with(title: "Assignment 1", author: "Linus Fricke",
    course: "Software Security", semester: "Winter Semester 2026/27")

#show <nonumber>: set heading(numbering: none)

#block(include "content/00-ai-statement.typ")<no-wc>

#outline()
#pagebreak()
#include "content/01-description.typ"
#include "content/02-functionality.typ"
#pagebreak()
#include "content/03-architecture.typ"
#pagebreak()
#include "content/04-trust-boundaries.typ"
#include "content/05-design-principles.typ"
#pagebreak()
#include "content/06-security-gates.typ"
#include "content/07-vulnerabilities.typ"
#include "content/08-production-changes.typ"

#block([Total words: #total-words])<no-wc>

#pagebreak()
#show: appendix
#include "appendix/01-ssdlc.typ"