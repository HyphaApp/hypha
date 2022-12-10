# Wagtail in Hypha

Wagtail is used in Hypha to construct and manage forms, pages, users and user roles via an admin interface (and code). In other words, Hypha uses Wagtail to build pages (using `blocks`), modify view-level behavior (using `hooks`), and create an admin interface for customizing settings like user permissions.

Hooks: modifying the view-level behavior 

- Used in Hypha for copied round pages

Blocks: components used to build the views and input fields for webpages. 

Wagtail blocks are used to construct the main streamfield block to be inherited by Pages (`StoryBlock`) — composed of:

- `ImageBlock`
- `DocumentBlock`
- `QuoteBlock`
- `BoxBlock`
- `MoreBlock`
- `ApplyLinkBlock` 

## What does it mean for a `Staff` role to have Wagtail Admin access? 
As a Wagtail Admin, you’re able to oversee user accounts and manage the level of access for different users. The role is similar to being an architect of a fund or lab — you can create and maintain a fund or lab. Whether that be choosing a workflow structure, designing application forms, or managing user role permissions.

From field guide: “The WagTail Admin is your "back office" for setting up form applications and publishing Funds. This interface is also where you could set different levels of permissions and access for user roles or groups.“