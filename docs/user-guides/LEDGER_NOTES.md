# ARDC Ledger Functionality

## Requested and approved amounts

Negative amounts are allowed in case the grantee needs to repay.
Wide currency amounts are allowed in cases of strange or inflated currencies.
The currency code is left optional and relatively unconstrained in case of new
or unofficial currencies.

## Contracts total on the All Projects table and dashboards

The All Projects table at `apply/projects/all/` and the projects tables on
the staff, contracting, and applicant dashboards show a "Contracts total"
column with the sum of the approved amounts recorded on each project's
contracts, followed by the currency code when all of those amounts share one
currency code. When a project's approved amounts do not share a single
currency code — including coded amounts alongside uncoded amounts — the
column shows "Multiple currencies" instead of a total. A project with no
approved amount entered shows "—" because absence is not zero; a sum that
genuinely totals zero shows as 0.00. The All Projects table's CSV export
shows the same values with locale-neutral number formatting.

The column is only present when `PROJECTS_PAYMENTS_FLOW` is
`DISBURSEMENTS`; in the `INVOICING` and `DISABLED` flows it is neither
computed nor shown (table, dashboards, CSV).
