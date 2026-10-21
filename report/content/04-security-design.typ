= Chosen Trust Boundaries
This chapter outlines and explains the security design decisions made during the design and implementation of the application. It also describes the chosen trust boundaries within the application as well as the its dependencies.

== Token-based Authentication
For both the user-facing Application API and the internal services _Resource Service_ and _Export Service_ use Json Web Tokens (JWT) for authentication and authorization. The tokens are created by the Application API, acting as the central authentication authority of the application and proxy of every API request a user sends.

The token distinguishes between two types of tokens: _user tokens_ and _system tokens_. User tokens are created for users of the application, while system tokens are created for the internal services to communicate with each other or relaying requests.
Each token contains the user id of the associated user, the role of the user and an expiration timestamp of the token. The role of the user is either _user_ or _admin_, as this is sufficient for the scope of this application. However, it could be extended to include more roles if required in the future.

Additionally, the tokens are signed using an assymetric key pair. The private key is only known to the Application API, while the public key is distributed across all internal services. The services verify both the signature and the expiration timestamp of the token to ensure its validity before processing any requests.

== Inter-Service Communication
The backend services are designed to only accept requests containing a valid system token, but not user tokens. This ensures that even if one of the services is compromised, the attacker cannot use a tapped user token to access the other services, which are normally not accessible to users.

In addition to the id and role of the associated user (which a token always contains), contain system tokens also the action that the service is allowed to perform.
This ensures that one service token is limited to a specific user and action, which reduces the risk of exposure of sensitive data in case of a compromised service or token.

Furthermore, the service tokens expire after ten minutes and can only be used once, which further reduces the risk of exposure of sensitive data. This one time usage is currently implemented by a cache in the service, which stores the used tokens for ten minutes and denies any requests with a used token.

== Authorization
While the Application API stores and authenticates the users, the internal services are responsible for authorizing the requests they receive, respectively the Resource Service in this case. This is done by checking the user id and role of the user contained in the system token against the requested action and resource.

== Dependencies
To prevent supply chain attacks as well as ensuring the exact behaviour of the application, the installation of the dependencies when running tests in the CI/CD pipelines as well as when building the container images of the application, the hashes of the dependencies are compared against the expected hashes, stored along with the desired version of the dependency. If the hashes do not match, the build or test process is aborted and the issue logged accordingly in the pipeline results.

Unfortunately, this is not possible for the CSV-file creation dependency, as it shipped as a directory in this repository, containing the source code and not as a prebuilt package. The initial intent was to build the dependency, generate a hash and then comparing a newly built version of the dependency against the expected hash. However, package contains, among other things, the timestamp of the build. This can be overriden using the environment variable `SOURCE_DATE_EPOCH` and setting it to a fixed value, e.g. the last changed date of the dependency directory. While this resulted in a static hash value both in the local and CI/CD build, the hash values still differed between the two environments. This is likely due to the different build environments and metadata. Due to the limited timeframe of the assignment, it was decided to not further investigate this issue and instead install the dependency from the directory in the repository, hence without building the wheel before and without verifying the hash of the dependency. In a production or real-world scenario, the package (wheel) of the dependency would be published to a (private) package repository, hence being static and the hash being verifiable like the other dependencies.