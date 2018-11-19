## Security

We take security very seriously at the Open Technology Fund. We welcome any peer review of our 100% open source code to ensure the information submitted through this platform or other who rely upon it is not compromised or that hacked.

### Where should I report security issues?

In order to give the community time to respond and upgrade we strongly urge you report all security issues privately. Please use our [vulnerability disclosure program at Hacker One](https://hackerone.com/otf) to provide details and repro steps and we will respond ASAP. If you prefer not to use Hacker One, email us directly at `team@opentech.fund` with details and repro steps. Security issues *always* take precedence over bug fixes and feature work. We can and do mark releases as "urgent" if they contain serious security fixes.

For a list of recent security commits, check [our GitHub commits prefixed with SECURITY](https://github.com/opentechfund/opentech.fund/search?utf8=%E2%9C%93&q=SECURITY&type=Commits).

### Password Storage

This application relies upon [Django's good use](https://docs.djangoproject.com/en/2.1/topics/auth/passwords/) of the PBKDF2 algorithm to encrypt salted passwords. This algorithm is blessed by NIST. Security experts on the web [tend to agree that PBKDF2 is a secure choice](http://security.stackexchange.com/questions/4781/do-any-security-experts-recommend-bcrypt-for-password-storage).

### Security in Django

For more information on the security features within this application, please see [Security in Django](https://docs.djangoproject.com/en/2.1/topics/security/), which includes information on:

* Cross site scripting (XSS) protection
* Cross site request forgery (CSRF) protection
* SQL injection protection
* Clickjacking protection
* SSL/HTTPS
* Host header validation
* Session security
* User-uploaded content 
* Additional security topics
