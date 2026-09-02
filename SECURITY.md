# Security

We take security very seriously. We welcome any peer review of our 100% open source code to ensure the information submitted through this platform or other who rely upon it is not compromised or that hacked.

## Supported versions

Security fixes are made on `main` and released from there. We do not backport them, so only the latest minor release is supported. Anything older is fixed by upgrading.

If you are running an older version, please upgrade before reporting — the problem may already be fixed. Deployers who want to hear about security releases as they happen should watch [releases](https://github.com/HyphaApp/hypha/releases) on GitHub.

## Where should I report security issues?

In order to give the community time to respond and upgrade we strongly urge you report all security issues privately.

Please e-mail disclosure@opentech.fund with details and reproduction steps. Expect an response within a few working days. Security issues *always* take precedence over bug fixes and feature work. We can and do mark releases as "urgent" if they contain serious security fixes.

For a list of recent security commits, check [our GitHub commits prefixed with SECURITY](https://github.com/HyphaApp/hypha/search?utf8=%E2%9C%93&q=SECURITY&type=Commits).

## What counts as a security issue

Hypha is software that other organisations install and run themselves. Some things that look like vulnerabilities in a live site are settings on that site rather than faults in the code, and those we cannot fix for you.

In scope is anything in this repository that lets someone:

* see submissions, reviews, determinations, projects or personal data they have no role-based right to see;
* act as another user, or gain a role they were not granted;
* bypass authentication, two-factor authentication, or the password reset flow;
* inject script or markup that runs in another user's session — particularly where a lower-privileged user can reach a staff or admin one;
* read or write files on the server, or upload content that is served back in a dangerous way;
* get more out of the API, search or export routes than their role allows.

Out of scope, and better raised elsewhere:

* the configuration of a particular deployment — TLS versions and ciphers, HTTP security headers, a weak or shared `SECRET_KEY`, `DEBUG` left on, storage buckets left open. Raise these with whoever runs that site; our [deployment documentation](https://docs.hypha.app/setup/deployment/production/stand-alone/) covers what needs setting.
* known vulnerabilities in our dependencies with no demonstrated effect on Hypha. Report those upstream. If you can show the flaw is reachable through Hypha, that is in scope and we want to hear about it.
* findings produced by pointing a scanner at a site, with nothing behind them to show an attacker could do anything.

Two things sit in between. Staff and administrators can write HTML in several places by design, so script injection that only a privileged user can set off is a real bug we will fix, but a low-severity one rather than an urgent release. Missing rate limits and similar hardening gaps are worth telling us about too — we would usually handle them as normal issues in the open rather than as an advisory.

If you are unsure which side of the line something falls on, e-mail us anyway and say so. We would far rather read a report that turns out to be out of scope than miss one that was not.

## Testing safely

Please test against your own installation. The [development setup guide](https://docs.hypha.app/setup/deployment/development/stand-alone/) will get you a local copy with test data.

Do not test against a deployment you do not run yourself. Hypha is used by organisations whose applicants are often in difficult and sometimes dangerous circumstances, and a live instance holds their real names, contact details and unpublished applications. Probing someone else's site risks exposing the people this software exists to protect, and the operator has no way of telling your testing apart from an attack. If a flaw can only be demonstrated against a live site, say so in your report and we will arrange something with the operator rather than have you go ahead.

On any deployment that is not yours, do not:

* access, download or retain data that is not your own;
* modify or delete data, or degrade the service for its users — no load testing, no automated scanning, no brute forcing;
* attempt social engineering, phishing or physical access against staff or applicants;
* keep access once you have shown the point, or share what you found with anyone before the advisory is published.

We will not pursue or support legal action against anyone who reports a vulnerability to us in good faith, stays within the boundaries above, and gives us reasonable time to fix the problem before saying anything publicly. If someone else takes action over research that followed these rules, we will say plainly and publicly that the work was done in good faith.

We cannot extend that assurance to other people's deployments, as they are not ours to speak for. This is not a paid bug bounty programme, but we will credit you in the advisory if you would like us to.

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
