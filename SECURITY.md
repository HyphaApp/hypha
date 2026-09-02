# Security

We take security very seriously. We welcome any peer review of our 100% open source code to ensure the information submitted through this platform or other who rely upon it is not compromised or that hacked.

## Where should I report security issues?

In order to give the community time to respond and upgrade we strongly urge you report all security issues privately. Only the latest minor release is supported so upgrade before reporting. Please e-mail disclosure@opentech.fund with details and reproduction steps. Security issues *always* take precedence over bug fixes and feature work. We can and do mark releases as "urgent" if they contain serious security fixes.

For a list of recent security commits, check [our GitHub commits prefixed with SECURITY](https://github.com/HyphaApp/hypha/search?utf8=%E2%9C%93&q=SECURITY&type=Commits).

## What we do when a serious security issue is found

This is the checklist we work through when a serious security issue is reported in Hypha. It exists so everyone involved can see what has already happened and what comes next — copy it into the draft advisory and tick items off as they are done, with a note of who did each one.

One maintainer owns the report until the advisory is published. If that cannot be you, say so early so someone else can pick it up. Nothing about the issue goes in a public issue, pull request, commit message or chat channel until step 9.

1. **Acknowledge the report.** Reply to the reporter within a few working days, thank them, and let them know someone is looking at it. Keep the conversation in e-mail or in the advisory.
2. **Confirm and assess.** Reproduce the issue. Work out what an attacker can actually do, and how serious it is (low / moderate / high / critical). If it turns out not to be a security issue, tell the reporter and handle it as a normal bug in the open.
3. **Open a draft security advisory.** On GitHub: *Security → Advisories → New draft security advisory*. Fill in the affected versions, severity and description, and request a CVE while you are there — GitHub issues the identifier and it stays private until the advisory is published. From here on this is where discussion, decisions and progress are recorded.
4. **Write the fix privately.** Use the private fork GitHub creates from the draft advisory. Keep the fix as small and focused as it can be, and add a regression test so the bug cannot come back.
5. **Get the fix reviewed.** At least one other maintainer reads it, and the reporter gets a chance to check that it really closes the hole. Still all in private.
6. **Agree a release date.** Pick a date and tell the reporter. Two weeks from confirmation is a reasonable default — sooner if the issue is being exploited, later only if the fix is genuinely hard.
7. **Give deployers a heads-up.** A few days before the release, e-mail known Hypha operators to say a security release is coming on that date, with the severity but without the details, so they can plan the upgrade.
8. **Release the fix.** Merge, tag and publish the release. Prefix the commit with `SECURITY` and label the pull request `Type: Security` so it lands in the right section of the release notes. Say plainly in the notes that this release contains a security fix and should be applied promptly.
9. **Publish the advisory.** Do this right after the release goes out. Credit the reporter by name if they want it, and link to the fix and the release.
10. **Tell people.** Announce the release in the community channels and anywhere else deployers look. State the affected versions, the fixed version, and anything they need to do beyond upgrading (rotating secrets, checking logs, and so on).
11. **Look back.** Once things are calm, check whether the same mistake exists elsewhere in the codebase, note anything worth adding to the tests or docs, and update this checklist if it did not match what actually happened.

## Password storage

This application use Django's default hasher (PBKDF2) and inherit its upgrades. For more information see [Password management in Django](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/).

## Security in Django

For more information on the security features within this application, please see [Security in Django](https://docs.djangoproject.com/en/5.2/topics/security/), which includes information on:

* Cross site scripting (XSS) protection
* Cross site request forgery (CSRF) protection
* SQL injection protection
* Clickjacking protection
* SSL/HTTPS
* Host header validation
* Session security
* User-uploaded content
* Additional security topics
