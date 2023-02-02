# Two Factor Authentication (2FA)

After an account is created, the user must activate their account by clicking the link sent to their email to reset their password. From there, 2FA can be activated/enabled. Authentication codes via a token generator app are required. 

2FA is implemented using `django-two-factor-auth` version `1.14.0`, which is built on top of the one-time password framework `django-otp` and Django’s built-in authentication framework `django.contrib.auth`.

2FA is required to view certain pages — without 2FA enabled, a user will only be able to view their own profile and log out. 

Staff admins can disable 2FA from the admin dashboard in the event that a user loses their phone. The process is as follows:

- User notifies support they’ve lost access to their TOTP device. 
- Staff authenticates user 
- Staff disables user’s 2FA 
- User is notified their 2FA is disables and they now have to re=enable it
- User recovers access to their account and is forces to re-enable 2FA
- User needs to pair new TOTP device to their account 
- User now has access to their account and 2FA is enabled 

In the case that a user does not have a smartphone (no camera to scan QR code) — the user flow is as follows: 

- User goes to set up 2FA page 
- User clicks on Advanced dropdown 
- User copies otpauth url in string format and pastes into password manager or any TOTP (time-based one time password) application. 
- User receives secret token from TOTP application / pass manager 
- User pastes secret token into hypha to enable 2FA on their account.
