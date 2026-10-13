= Project Description
A *budget application* to manage income and expenses across multiple named buckets / accounts per user. The user role can create and delete its own buckets and add / remove expenses from it, while the admin role can delete all buckets. Lastly, the expenses of a bucket can be exported as a CSV-file, which offers the possibility to use a dependency for the generation of a CSV file.

This project was chosen as it has a tightly limited scoped, while still being broad enough to implement the different required securiry vulnearbilities.

This results in the following application domains:

#figure(caption: "Application domains", table(
  columns: 3,
  table.header([Application], [Protected resources], [External dependencies]),

  [Budget tracker],
  [
    - Buckets
    - Expenses
  ],
  [
    - CSV-file creator
  ],
))

// - export per bucket (vuln /export/\<bucketname\> --> redirect to unauthenticated /download/\<bucket-id> )
// - vuln: create admin account by specifying role: admin
// - vuln: do not verify signature of JWT --> user id / role can be forged
// - vuln: sql injection????