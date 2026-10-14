# Disbursements Functionality

## Requested and approved amounts

Negative amounts are allowed in case the grantee needs to repay.
Wide currency amounts are allowed in cases of strange or inflated currencies.
The currency code is left optional and relatively unconstrained in case of new
or unofficial currencies.

## Contracts and disbursed totals on the All Projects table and dashboards

The All Projects table at `apply/projects/all/` and the projects tables on
the staff, contracting, and applicant dashboards show a "Contracts total"
column with the sum of the approved amounts recorded on each project's
contracts, and a "Disbursed total" column with the sum of the disbursement
amounts recorded against those contracts (negative disbursements, for
repayments, net out). Each column is followed by the currency code when all
of its underlying amounts share one currency code; when they do not —
including coded amounts alongside uncoded ones — that column shows
"Multiple currencies" instead of a total. A project with no approved amount
entered, or with no disbursements, shows "—" because absence is not zero; a
sum that genuinely totals zero shows as 0.00. The All Projects table's CSV
export shows the same values with locale-neutral number formatting.

Both columns are only present when `PROJECTS_PAYMENTS_FLOW` is
`DISBURSEMENTS`; in the `INVOICING` and `DISABLED` flows they are neither
computed nor shown (table, dashboards, CSV).
