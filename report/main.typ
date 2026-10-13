#import "template/layout.typ": writeup
#import "@preview/wordometer:0.1.6": word-count, total-words

#show: word-count.with(exclude: (figure, <no-wc>))

#show: writeup.with(title: "Assignment 1", author: "Linus Fricke",
    course: "Software Security", semester: "Winter Semester 2026/27")



#block([Total words: #total-words])<no-wc>