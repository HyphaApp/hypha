The WagTail Admin is your "back office" for setting up form applications and publishing Funds. This interface is also where you could set different levels of permissions and access for user roles or groups. You could use the admin menu (or explorer menu)to navigate through different sections of the WagTail Admin.

!!! info "What does it mean for a `Staff` role to have Wagtail Admin access?" 
    As a Wagtail Admin, you’re able to oversee user accounts and manage the level of access for different users. The role is similar to being an architect of a fund or lab — you can create and maintain a fund or lab. Whether that be choosing a workflow structure, designing application forms, or managing user role permissions.

    From field guide: “The WagTail Admin is your "back office" for setting up form applications and publishing Funds. This interface is also where you could set different levels of permissions and access for user roles or groups.“


## Admin menu

### Hypha custom

- Apply
- Rounds: Create rounds
- Sealed Rounds
- Funds: Create fund
- Labs: Create lab 
- Request for Partners: RFP application
- Application Forms
- Review Forms
- Determination Forms
- Category Questions: Application questions with multiple options for users to select.
- Screening Statuses: For metadata related to the initial screening stage. 
- Reviewer Roles: Adding reviewer roles.
- Meta Terms: For metadata, such as tags, thumbnail image and ... “and” - The results must match all terms (default for database search).
- Manage

### Wagtail default settings

- Search: Wagtail provides a comprehensive and extensible search interface. In addition, it provides ways to promote search results through “Editor’s Picks”. Wagtail also collects simple statistics on queries made through the search interface.
- Reports: Reports are views with listings of pages matching a specific query. They can also export these listings in spreadsheet format. They are found in the Reports submenu
- Locked Pages
- Workflows
- Workflow tasks
- Site history: Generates a report of user action logs.
- Aging page
- Public Site
- Images
- Documents: Store documents like reports for blog posts 
- Snippets: Snippets allow you to create elements on a website once and reuse them in multiple places. Then, if you want to change something on the snippet, you only need to change it once, and it will change across all the occurrences of the snippet. How snippets are used can vary widely between websites. 
- Taxonomies

## Settings

### Hypha custom

- Cookie consent settings: Cookie consent settings allow us to store your settings and preferences
- User settings: Users could add a consent checkbox on login form and include extra text on login form
- Vendor form settings
- Project settings: Creating forms in Projects
- Determination messages: Pre-populated text
- Determination settings: Creating determination forms
- Reviewer settings: Manage submissions reviewers should have access to
- Application settings: Extra text on application landing page

### Wagtail default settings

- Workflows: Workflow states represent the status of a started workflow on a page
- Workflow tasks: Represents the ordering of a task in a specific workflow.
- Users: Adding, modifying, or removing user profiles. 
- Groups: Create user groups with a specific set of permissions
- Sites: Managing the list of sites served by this Wagtail instance. Define settings that are editable by administrators in the Wagtail admin. These settings can be accessed in code, as well as in templates.
- Collections: Access to specific sets of images and documents can be controlled by setting up ‘collections’. By default all images and documents belong to the ‘root’ collection, but users with appropriate permissions can create new collections through the Settings -> Collections area of the admin interface.
- Redirects: When dealing with publishing and unpublishing pages you will eventually need to make redirects. A redirect ensures that when a page is no longer available (404), the visitor and search engines are sent to a new page. Therefore the visitor won’t end up in a breaking journey which would result in a page not found.
