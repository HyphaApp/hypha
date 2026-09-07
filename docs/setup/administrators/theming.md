# Theming Hypha

Hypha's interface is built with [Tailwind CSS](https://tailwindcss.com/) and
[daisyUI](https://daisyui.com/). Every colour, corner radius and border width comes from a small
set of CSS custom properties, and those properties can be overridden from a single custom
template — no fork, no frontend build, no recompiled assets.

A handful of overridden values is enough to make Hypha look like it belongs next to your
organisation's other web properties, without touching a single Hypha template.

Two themes are defined, `light` and `dark`, and visitors switch between them (or follow their
operating system) with the theme toggle in the header. Whatever you change, change it in both.

## How the colours are organised

Hypha's defaults live in `hypha/static_src/tailwind/base/themes.css`. You do not need to edit
that file — but it is worth knowing how it is put together, because it explains why so little
CSS is needed to re-theme the whole application.

**1. The brand ramp.** A single brand colour, and ten shades derived from it:

```css
:root {
  --color-brand: oklch(56.2% 0.102 243);
  --color-brand-base: 0.05;
  --color-brand-10: /* … derived from --color-brand … */;
  /* --color-brand-20 through --color-brand-100 */
}
```

The shades are generated from `--color-brand` with CSS relative colour syntax, so one colour
produces a consistent light-to-dark ramp.

**2. The two daisyUI themes.** Each theme sets its own colours, mostly daisyUI defaults, with the
primary colour taken from the brand ramp — a lighter step in dark mode, a slightly darker one in
light mode:

```css
@plugin "daisyui/theme" {
  name: "dark";
  --color-primary: var(--color-brand-50);
  /* … */
}

@plugin "daisyui/theme" {
  name: "light";
  --color-primary: var(--color-brand-60);
  /* … */
}
```

The important consequence: `--color-brand` is defined **once**, outside both themes, so
overriding that one value re-colours both themes at once.

## What each colour controls

| Variable | Where you see it in Hypha |
| --- | --- |
| `--color-primary` | Primary buttons, active navigation underline, link hover colour, primary badges. The most visible brand colour. |
| `--color-primary-content` | Text and icons drawn *on top of* the primary colour. Must contrast with `--color-primary`. |
| `--color-secondary` | Secondary buttons and badges. |
| `--color-base-100` | Page and card backgrounds. |
| `--color-base-200` | Panel, table header and sidebar backgrounds. |
| `--color-base-300` | Borders, dividers and loading placeholders. |
| `--color-base-content` | Body text. |
| `--color-neutral` | A few high-contrast surfaces. |
| `--color-info`, `--color-success`, `--color-warning`, `--color-error` | Status badges, alerts and form validation messages. Best left close to the conventional blue/green/amber/red so their meaning stays obvious. |
| `--color-accent` | Not currently used by any Hypha template — changing it has no visible effect. |
| `--radius-selector`, `--radius-field`, `--radius-box` | Corner radius of checkboxes/toggles, inputs/buttons, and cards/modals. All `0.25rem` by default. |
| `--border` | Default border width. |

## Where to put your overrides

Create the file `hypha/templates_custom/includes/head_end.html`.

This template is included at the very end of `<head>`, after Hypha's own stylesheets, and exists
precisely for additions like this. Anything you declare there wins over the defaults, for one of
two reasons: the daisyUI theme values are emitted inside a `@layer base` cascade layer, and
unlayered styles beat layered ones whatever their specificity or order; the brand ramp
(`--color-brand` and its shades) is emitted unlayered in `:root`, and your `:root` rule wins on
source order because it comes later in the document.

Both routes depend on your CSS staying **unlayered**, so do not wrap it in a cascade layer of
your own — `@layer custom { :root { --color-brand: … } }` would lose to the unlayered brand ramp
and be silently ignored. Nothing needs to be recompiled and no `collectstatic` run is needed —
the change takes effect as soon as the file is in place.

Everything below goes inside that file.

## Change the brand colour

For most organisations, this is the whole job:

```html
<style>
    :root {
        --color-brand: oklch(53.2% 0.106 162.8); /* forest green */
    }
</style>
```

Both themes pick up the new colour, because both derive their primary from the ramp. Primary
buttons, the active navigation underline, link hover states and primary badges all change
together, in light and dark mode.

Some starting points, with the equivalent hex value for reference:

| Brand | Hex | `--color-brand` |
| --- | --- | --- |
| Hypha default (blue) | `#2378a8` | `oklch(56.2% 0.102 243)` |
| Forest green | `#1B7F5A` | `oklch(53.2% 0.106 162.8)` |
| Teal | `#0F766E` | `oklch(51.1% 0.086 186.4)` |
| Deep purple | `#6C3FBF` | `oklch(49.3% 0.190 294.6)` |
| Navy blue | `#1D4ED8` | `oklch(48.8% 0.217 264.4)` |
| Warm red | `#C8442A` | `oklch(56.9% 0.173 33.1)` |

To convert your own brand colour, paste the hex value into [oklch.com](https://oklch.com/). The
three numbers are lightness, chroma (saturation) and hue. Keep lightness somewhere around
`50–60%` so the derived ramp has room to go both lighter and darker; if your brand colour is very
light or very dark, take its hue and chroma but pick a mid lightness here.

You can also override `--color-brand-base` in the same block. It controls how much colour is left
at the extreme ends of the ramp: raise it towards `0.1` for more saturated tints and shades,
lower it towards `0` for more neutral ones.

## Change individual colours

To go further than the brand colour, override the daisyUI variables directly. These are set
*per theme*, so you must override them per theme too — otherwise your light-mode value leaks into
dark mode.

There are three cases to cover, not two. A visitor who has never touched the theme toggle is in
auto mode, and auto mode sets no `data-theme` attribute at all — it lets the operating system
decide, through a `prefers-color-scheme` media query:

```html
<style>
    /* Light theme, and auto mode on a light OS */
    :root,
    [data-theme="light"] {
        --color-primary: oklch(48% 0.11 162.8);
        --color-primary-content: oklch(100% 0 0);
        --color-secondary: oklch(45% 0.04 257);
    }

    /* Dark theme */
    [data-theme="dark"] {
        --color-primary: oklch(70% 0.13 162.8);
        --color-primary-content: oklch(18% 0.02 162.8);
        --color-secondary: oklch(64% 0.03 229);
    }

    /* Auto mode on a dark OS */
    @media (prefers-color-scheme: dark) {
        :root:not([data-theme]) {
            --color-primary: oklch(70% 0.13 162.8);
            --color-primary-content: oklch(18% 0.02 162.8);
            --color-secondary: oklch(64% 0.03 229);
        }
    }
</style>
```

Dark mode normally wants a lighter, less saturated version of the same colour, so it does not
glare against the dark background.

!!! warning

    Setting a per-theme variable on `:root` alone applies it to *every* case. Your declarations
    are unlayered and Hypha's theme rules sit in `@layer base`, so yours win even where Hypha's
    selector is the more specific one — a bare `:root` overrides the dark theme too.

    Auto mode is the easiest of the three to miss, because `[data-theme="dark"]` cannot match a
    visitor who has no `data-theme` attribute — but your `:root` block can. Leave the third block
    out and an auto-mode visitor on a dark operating system gets Hypha's dark backgrounds with
    your *light* colours on top. That is why the `@media (prefers-color-scheme: dark)` block above
    repeats the dark values: both blocks are yours, and `:root:not([data-theme])` is more specific
    than `:root`, so the dark values win in auto mode whichever order you write them in.

    `--color-brand` is the exception — it is not part of either theme, so `:root` is the correct
    place for it and it never needs repeating.

A softer, warmer set of backgrounds is a common second change. It tints every panel, table and
card in the application. This one changes the light theme only, so target light explicitly rather
than using `:root` — `:root` would carry the pale backgrounds into dark mode as well:

```html
<style>
    [data-theme="light"] {
        --color-base-100: oklch(99% 0.004 85);  /* off-white page background */
        --color-base-200: oklch(97% 0.006 85);  /* panels and table headers */
        --color-base-300: oklch(93% 0.008 85);  /* borders and dividers */
    }

    /* Auto mode on a light OS */
    @media (prefers-color-scheme: light) {
        :root:not([data-theme]) {
            --color-base-100: oklch(99% 0.004 85);
            --color-base-200: oklch(97% 0.006 85);
            --color-base-300: oklch(93% 0.008 85);
        }
    }
</style>
```

Squarer or rounder corners are a one-liner. These are meant to apply everywhere, so here `:root`
is exactly what you want — it covers auto mode on both kinds of operating system:

```html
<style>
    :root,
    [data-theme="light"],
    [data-theme="dark"] {
        --radius-field: 0.5rem;   /* inputs and buttons */
        --radius-box: 0.75rem;    /* cards and modals */
    }
</style>
```

## Larger changes: use a stylesheet file

Once you have more than a few declarations, move the CSS out of the template and into a file.
Anything under the `public/` directory is served as a static file, so
`public/css/theme-custom.css` can be linked from the same `head_end.html`:

{% raw %}
```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/theme-custom.css' %}">
```
{% endraw %}

Run `collectstatic` after adding or changing that file in production:

```bash
python manage.py collectstatic --noinput --settings=hypha.settings.production
```

## Alternative: edit the theme source and rebuild

If you already run Hypha from your own fork and build the frontend assets as part of your
deployment, you can change the defaults directly in
`hypha/static_src/tailwind/base/themes.css` instead. Edit `--color-brand` in the `:root` block,
or set variables inside the two `@plugin "daisyui/theme"` blocks:

```css
@plugin "daisyui/theme" {
  name: "light";
  /* … */
  --color-primary: oklch(48% 0.11 162.8);
  --color-primary-content: oklch(100% 0 0);
  --color-base-100: oklch(99% 0.004 85);
  /* … */
}
```

Then rebuild. In development, `make serve` watches the file and rebuilds as you save. For a
production deployment:

```bash
npm run build
python manage.py collectstatic --noinput --settings=hypha.settings.production
```

This is more work to carry across upgrades, but it is the only approach that also covers the 400
and 404 error pages, which are standalone templates that do not include `head_end.html`.

## Logo and favicon

Colours are only part of blending in.

**The site logo** needs no code at all. Upload it in Wagtail admin under
`Settings` -> `System settings`, where you can set a default logo, a separate mobile logo, and
the URL the logo links to. Without one, Hypha falls back to its own logo.

**The favicons** are static files in `hypha/static_src/images/favicons/`, and the `<link>` tags
for them are in `base.html`. Replacing them means either swapping those source files and
rebuilding, or overriding `base.html` itself —
[realfavicongenerator.net](https://realfavicongenerator.net/) produces the full set.

Surrounding markup such as `hypha/templates/includes/header-logo.html` can be overridden like any
other template — see [Overriding templates](overriding-templates.md).

## Before you go live

- **Check both themes.** Use the theme toggle in the header, and check it in a browser set to
  dark mode as well.
- **Check the contrast.** Most colours have a matching `--color-*-content` for text drawn on top
  of them, and the `base-*` backgrounds share `--color-base-content`. If you darken
  `--color-primary`, its content colour probably needs to be white; if you lighten it, black.
  Aim for a contrast ratio of at least 4.5:1 — [oklch.com](https://oklch.com/) shows the ratio as
  you adjust a colour, and Hypha's [accessibility notes](../../references/accessibility.md) cover
  the wider commitments.
- **Keep the status colours recognisable.** Applicants and reviewers rely on red meaning
  rejected and green meaning approved.
- **The Wagtail admin keeps its own look.** These variables style the applicant, reviewer and
  staff interface; the Wagtail CMS admin is styled separately — see
  [Wagtail admin](../../references/wagtail-admin.md).
