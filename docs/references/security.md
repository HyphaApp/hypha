In 2021, Radically Open Security carried out a penetration test for the Hypha web app and its user roles. This test resulted in 1 elevated, 5 moderate and 13 low-severity issues. This document outlines the details of the findings and their implemented solutions.

#### Elevated Threat Level Issues 

1. Several form fields that use TinyMCE allow the input of dangerous characters resulting in XSS when editing a form.
    - This would allow an unauthenticated or low privileged user to send a malicious XSS payload (e.g. containing session hijacking, credential stealing, malware) to high privileged users (e.g. staff members and admins). This could result in gaining access to high privileged accounts which would lead to accessing restricted data.
> Update: This issue was resolved in PR [#2495](https://github.com/HyphaApp/hypha/pull/2495) which updated TinyMCE to newer version, PR [#2508](https://github.com/HyphaApp/hypha/pull/2508), using the invalid elements attribute of TinyMCE to validate input, and PR [#2518](https://github.com/HyphaApp/hypha/pull/2518) which disabled the TinyMCE `contextmenu`.



#### Moderate Threat Level Issues

1. `opentech.fund` and `apply.opentech.fund` accept connections encrypted using TLS 1.0 and/or TLS 1.1. TLS 1.0 has a number of cryptographic design flaws. Modern implementations of TLS 1.0 mitigate these problems, but newer versions of TLS (TLS 1.2) are designed against these flaws and should be used whenever possible.
    - Accepting TLS 1.0 and TLS 1.1 makes the data in transit vulnerable to attacks in which an attacker can capture the
encrypted data and decrypt it.
> Update: This issue was resolved by disabling TLS 1.0 and 1.1


2. `opentech.fund` and `apply.opentech.fund` support insecure 3DES ciphers.
    - An attacker with a MitM (Machine in the Middle) position can potentially capture and intercept communication between server and clients.
  > Update: This issue was resolved by disabling the use of the insecure 3DES ciphers.


3. There are no additional authentication checks, such as requiring a password or two-factor token, preventing logged in users from changing their email address. Email addresses are used for account recovery operations that can be abused by attackers.
    - An attacker who gains temporary access to a victim's account (be it by exploiting a different vulnerability or by gaining physical access to the victim's machine, a common scenario in office settings) can change the victim's email address to a different address controlled by the attacker, enabling them to take full control of the victim's account by using the forgot password functionality.
> Update: Resolved with PR [#2653](https://github.com/HyphaApp/hypha/pull/2653) ensuring the current password or a two-factor authentication token is required whenever a user attempts to change their email address.


4. Two-factor authentication (2FA) can be disabled without providing the current password.
    - This could allow an adversary to disable the user's 2FA, for instance by using a XSS attack or other attack.
> Update: Resolved with PR [#2661](https://github.com/HyphaApp/hypha/pull/2661) requiring the user to provide their current password or token before 2FA can be disabled to add an additional layer of security.


5. The application incorrectly validates input that can affect the control flow or data flow of a program
    - Allowing dangerous input could lead to XSS
> Update: Resolved with PR [#2508](https://github.com/HyphaApp/hypha/pull/2508 ) using invalid elements attribute of TinyMCE to validate input. 


#### Low Threat Level Issues

1. Obsoleted CBC ciphers
    - TLS misconfiguration - `apply.opentech.fund` are configured to support cipher block chaining encryption (CBC) 
> Status: At the time of the report, unresolved.

2. Open redirect
    - Subscribe newsletter is vulnerable to open redirection.
> Recommendation: Do not use user input for URLs. If dynamic URLs are required, use whitelisting. 

3. Insecure password reset 
    - The password reset functionality is by default set to 8 days and the reset token remains the same until it has been changed. The link does change after the password (including the same password) has been reset. 
> Update: Configured password reset timeout to a maximum of 1 hour.

4. Lack of anti-automation 
    - Someone can maliciously automate use of functionality such as password reset, 2FA, 2FA backup login, newsletter subscription, apply forms and user login. 200 password requests were issued within 5 seconds and resulted in a flooded mailbox. 
> Suggestion: Apply anti-automation on those features. One common way is implementing a Captcha and only show and enforce after a certain amount of requests per IP. 

5. XSS in footer 
    - The footer incorrectly validates input that results in cross-site scripting (XSS). This XSS can only be created and triggered by high-privileged users (staff and admin), which makes it low impact. However it is recommended to not allow XSS in the first place, since a successful attack could lead to session hijack, credential stealing, or infecting systems with malware.  


6. Low-privileged user able to purge CDN and cache 
    - Staff members (high-privileged users), editors and moderators do not see the purge CDN and cache functionality in the UI but are still able to use the functionality by using the following URLs:
        - `http://hypha.test:8090/admin/cache/`
        - `http://hypha.test:8090/admin/purge/`

7. XSS in `Used By`
    - The `Used By` field incorrectly validates input that results in XSS. This XSS can only be created and triggered by high-privileged users (staff and admin), which makes it low impact. However it is recommended to not allow XSS in the first place, since a successful attack could lead to session hijack, credential stealing, or infecting systems with malware.  


8. XSS in Reviewer Role 
    - This XSS can only be created and triggered by high-privileged users (staff and admin), which makes it low impact. However it is recommended to not allow XSS in the first place, since a successful attack could lead to session hijack, credential stealing, or infecting systems with malware.  


9. User Enumeration with Email Address Change 
    - Valid users can be found by abusing the Profile change email address functionality. 
> Recommendation: Modify the functionality to return only a generic response making it impossible to distinguish between a valid username and invalid username and implement a Captcha. 


10. XSS in Review Form 
    - This XSS can only be created and triggered by high-privileged users (staff and admin), which makes it low impact. However it is recommended to not allow XSS in the first place, since a successful attack could lead to session hijack, credential stealing, or infecting systems with malware.  


11. Django `SECRET_KEY` not random 
    - `SECRET_KEY` is hardcoded and using a default value. The secret key is used for all sessions if you are using any other session backend than `django.contrib.sessions.backends.cache`, or are using the default `get_session_auth_hash()`, all messages if you are using `CookieStorage` or `FallbackStorage`, all `PasswordResetView` tokens, and any usage of cryptographic signing, unless a different key is provided.
> Recommendation: Automatically generate Strong Random Secret key instead of using a static key.


12. Arbitrary document file upload 
    - No restrictions configured on the document file upload functionality. `.exe` files were successfully uploaded via the document upload functionality. 
> Recommendation: Verify all upload functionality. 


13. Outdated packages are in use 
    - `npm audit report` — found outdated packages which contain known vulnerabilities. Marked as low because it appears that no functionality is used in the current code that could exploit any of the vulnerabilities. 
