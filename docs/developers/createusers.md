# Create a new User

## The First User (_for Developers_):

The first user account is created when you install Hypha with this command:

```
python manage.py createsuperuser
```

The user created is an "administrator" role, a default Django role that bypasses any access restrictions, like 'root' on a Unix server.

This role should only be used by the person implementing/deploying Hypha for your organization, who may be part of the organization or may be an external contractor.


## Creating additional users

Creating additional users and assigning them Roles is done in Wagtail by someone with the Staff role.

> ℹ️ _Only users with the_ [_"Staff"_](../staff/user-roles/hypha_roles.md) _Role can do this_

### 1. From the Dashboard, click the "Apply admin" button

\[insert Sandbox\_dashboard\_Staff img here]

This takes you to the Wagtail dashboard (pictured below).

### 2. Click on "Settings" in the menu on the left side of the screen

This will bring up another sub-menu

### 3. Click "Users" within the "Settings" menu

Takes you to the Create Users page, which has two tabs (CALLED WHAT?)

### 4. Add user info (Name and contact)

In the \[NAME] Tab, add the user's name and contact email address

### 5. Select user Roles

In the \[Roles] tab, specify the level of access you want your user to have by giving them specific Roles (see [Roles documentation](../staff/user-roles/index.md) for more information)

### 6. Finish by clicking a button, I'm sure (just have to look again to remember what it's called)

!!! info "Reporting Issues"
    ⚠️ If you notice errors on this page, or would like to see content added, please: post on [we.hypha.app](https://github.com/HyphaApp/hypha-docs/tree/d18f0a73a801778bd0eae53bce657858317053ba/gettingstarted\_overview/we.hypha.app) OR  post a "New Issue" on the [Hypha documentation Github page](https://github.com/HyphaApp/hypha-docs/issues). **Make sure to include a link to this page in your post**.
