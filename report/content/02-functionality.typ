= Functional and non-functional requirements
The following *functional requirements* have been identified:
+ Multiple users must be able to authenticate, supporting at least one ordinary user and one administrator role.
+ Users must be able to create named buckets and add or substract expenses from them.
+ Users must be able to request an export of all expenses within a specific bucket.
+ The admin role must be able to perform a restricted action such as deleting someone elses bucket.
+ The export service must utilize an external dependency.

The following *non-functional requirements* have been identified through the context of the application as well as the requirements of the assignment:
+ *Architecture:* The application must run as a multi-tier application with the different components running as entirely different processes, i.e. different containers and communicating through explicit interfaces such as HTTP.
+ *Security:* The application must ensure security and strict separation of data, so an ordinary user cannot access, modify or delete other users buckets (contents).
+ *Security design principles:* The implementation must use at least three secure design principles.
+ *Automcation (CI/CD):* The software must be built, tested and validated using a CI/CD pipeline (_not just Jenkins, thanks TA for the clarification_) that automatically runs on every push or pull request creation and saves the results as artifacts. 