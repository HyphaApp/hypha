Hypha comes stock with a cookie banner indicating that only essential cookies are used. You can configure this banner to display information about analytics cookies in Wagtail Admin under `Settings` -> `Cookie banner settings`. 

It's possible to configure settings such as:

* Edit General cookie consent message
* Edit Essential cookies informational statement
* Enable & edit the analytics cookies informational statement

### Retrieving preferences

Cookie preferences are stored in the browser's local storage using the key `cookieconsent`, and can be globally retrieved via:

```js
localStorage.get('cookieconsent')
```

There are three valid values `cookieconsent` in local storage:

* `decline` - analytics cookies have been declined, only essential cookies should be used
* `accept` - all cookies are consented to
* `ack` - there are no analytics cookies and user accepts that only essential cookies are in use
* **null** - no selection has been made by the user in the cookie banner

On page load the cookie banner JavaScript snippet will check if cookie policies have changed (ie. the site originally only used essential cookies, user ack'd, then analytics cookies were enabled) and automatically reprompt the user with the new cookie options.

### Allowing the user to change cookie preferences

The functions to open and close the cookie consent prompts are globally exposed in the JavaScript and can be utilized via:

```js
// Open consent prompt
window.openConsentPrompt()

// Close consent prompt
window.closeConsentPrompt()
```

By default, there is a button in the footer that allows the user to re-open the cookie consent prompt:

```html
<a href="#" onclick="openConsentPrompt()">Cookie Settings</a>
```

This can be further configured in Wagtail Admin under `Settings` -> `System settings` -> `Footer content`.