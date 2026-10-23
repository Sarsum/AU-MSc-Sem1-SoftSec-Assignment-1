= Planted Vulnerabilities
The following vulnerabilities were intentionally planted in the source code of the application as part of the assignment:
1. *CWE-20 -- Improper Input Validation*: The application does not properly validate the user input during the creation of a new user, but just uses it directly to create the new database object: `db_user = DBUser(**user_dict)` (#link("https://github.com/Sarsum/AU-MSc-Sem1-SoftSec-Assignment-1/blob/main/application/api/app.py#L49", [`application/api/app.py` line 49])). This allows an attacker to either insert any username, including special characters, or to create a user with an empty username. While this does not directly lead to a security vulnerability, it could be exploited as a CWE-79 Cross-Site Scripting (XSS) vulnerability if a web interface was implemented for the application.
 
 However, the missing input validation and direct data usage leads to the user being able to create an user with the admin role assigned, bypassing the least privilege principle and overring the default user role assignment.

 This vulnerability can be exploited by sending a POST request to the `/users` endpoint with the following JSON payload:
 ```json
 {"username": "attacker","password": "password","role": "admin"}
```

 Patching this vulnerability is also comparatively easy, as it only requires not just passing all arguments into the user creation function, but instead only passing the username and password:
 
 ```python
 db_user = DBUser(username=user.username,
     password=hash_password(user.password))
 ```

 This ensures that the user role is always set to the default value, which is `user` in this case, and cannot be overridden by the user input.
#pagebreak()
2. *CWE-22 -- Path Traversal*: The resource service contains a path traversal vulnerability in the `get_export` function. Due to the files being saved in a separate directory for each user and having only the bucket name as name, an attacker can perform a path traversal attack without any further escape characters. The `get_export` function does not validate the `bucket_name` parameter, allowing an attacker to access files outside of the intended directory structure. This could lead to unauthorized access to sensitive files on the server. For example, an attacker can use the following request to access the resources service's source code: `GET /exports?bucket_name=..%2F..%2Fapp.py`.

 This vulnerability can be patched by validating the `bucket_name` parameter to ensure that it does not contain any path traversal characters or sequences. One way to do this is to parse it as a `pathlib.Path` object and retrieve just the name of the file, which will remove any path traversal characters. The patched code would look like this:
  ```python
  filename = Path(bucket_name).name
  ```
  Afterwards, the `filename` variable can be used to construct the file path, ensuring that only files within the intended directory structure can be accessed.

  Additionally, the user id should also be parsed the same way, even though it can only be set by the supposed-to-be trusted Application API. However, as a principle of defense in depth, all input should always be validated, even if it is coming from a trusted source.

3. *CWE-862 -- Missing Authorization*: The `get_transactions` function of the resource service does not implement any authorization checks, allowing valid system tokens for the `get_transactions` action to access any users transactions (#link("https://github.com/Sarsum/AU-MSc-Sem1-SoftSec-Assignment-1/blob/main/application/resource/app.py#L117-L126")). However, as the resource api is only accessible by the application api and not directly from the internet, attackers cannot directly exploit this vulnerability.

 Nevertheless, this vulnerability should be mitigated by implementing proper authorization checks to ensure that users can only access their own transactions. For example, this can be achieved by adding the following check to the database query:
 ```python
, DBBucket.user_id == token[0]
```

 This ensures that only the bucket belonging to the user initiating the export request is being returned, and hence only the transactions belonging to that user and bucket are being exported.

4. *Service Composition Vulnerability*: While the last vulnerability cannot directly be exploited by an attacker through the `GET /bucket/{bucket_name}/transactions` endpoint, it leads to an information disclure vulnerability due to the combination of the services. As the authorization checks are supposed to be handled by the resource service, neither the application api nor the resource service implement any checks and are not even able to due to the strict separation of duties. Hence, an attacker can include any existing bucket name in the export request to the application api, which will then be forwarded to the export service. The export service requests the raw data export from the resource service, transforms it into a CSV file and uploads it back to the resource service, into the resource folder of the attacker (the user initiating the export request). The resource service currently does not verify the ownership of a bucket when trying to download a file, as the export service should only be able to upload valid files when everything works correctly. Therefore, it could be plausible to add a test when uploading a file to the resource service, retrieving the bucket using the bucket name and verifying that the owner matches the user id of the request. However, this is only a possible additional test, while the main issue is the trust between the services in correlation with vulnerability 3, _CWE-862 -- Missing Authorization_.