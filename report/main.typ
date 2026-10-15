#import "template/layout.typ": writeup, appendix
#import "@preview/wordometer:0.1.6": word-count, total-words

#show: word-count.with(exclude: (figure, <no-wc>))

#show: writeup.with(title: "Assignment 1", author: "Linus Fricke",
    course: "Software Security", semester: "Winter Semester 2026/27")

#include "content/01-description.typ"
#include "content/02-functionality.typ"
#include "content/03-architecture.typ"

#block([Total words: #total-words])<no-wc>

#pagebreak()
#show: appendix
#include "appendix/01-ssdlc.typ"