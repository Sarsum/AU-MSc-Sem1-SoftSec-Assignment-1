#import "@preview/merman:0.4.0": mermaid

= Application Architecture
The application consists of three microservices in addition to the database storing all data:

#figure(caption: "Application microservices", table(
  columns: 3,
  table.header([*Component*], [*Functionality*], [*Security responsibility*]),

  [Application API],
  [User authentication],
  [Identify the user],

  [Resource Service],
  [Perform operations on the buckets (create bucket or manage \ expenses)],
  [Ensure operations are only performed on own buckets, or role is administrator],

  [Export Service],
  [Export expenses of a bucket using the CSV-file creation \ dependency],
  [Export only the data of the \ explicitly requested job],

  [CSV-file dependency],
  [Create CSV-file based on \ provided data],
  [N/A],
))

Due to the limited timeframe of the assignment, it has been decided to let the application API handle the creation of authentication tokens for users and systems as well.
Json Web Tokens (JWT) will be used, as they offer the possibility to add metadata such as the user / system id and an expiration date of the token.
In other cases, it could be moved to another microservice, which can then also be used to validate tokens periodically in case of long validity timeframes.

#let diagonal(body-r, body-l, width: auto, height: auto) = {
  box(
    width: width,
    height: height)[
      #place(top+right,body-r)
      #place(bottom+left,body-l)
      #line(start: (0%,0%),end: (100%,100%),stroke: 0.5pt)
  ]
}

== Access Control Matrix
This access control matrix shows the desired controls for the application, resulting in a very strict confidentiality of the user data while also enabling transfers of buckets by an administrator in case required / requested.
#figure(caption: "Access Control Matrix", table(
  columns: 4,
  table.header([*Action*], [*User -- owning Bucket*], [*User -- not owning bucket*], [*Administrator*]),

  [Create Bucket],
  [Allow],
  [Allow],
  [Allow],

  [Add Transaction],
  [Allow],
  [Deny],
  [Deny],

  [Delete Bucket],
  [Allow],
  [Deny],
  [Deny],

  [Request Bucket],
  [Allow],
  [Deny],
  [Deny],

  [Change Bucket Owner],
  [Deny],
  [Deny],
  [Allow],
))