# Proposal

## Why

An issued invoice without Spanish VAT (a service to a client in another EU country or outside the EU) passed the register checks, then the 303 and 390 builders stopped with "VAT rate 0 % is not 4, 10 or 21". No file was produced for the quarter.

## What Changes

- Issued invoices get a `kind`: `domestic` (default; notes written before this change read as `domestic`), `eu-services` or `non-eu-services`.
- The register refuses a `domestic` invoice whose rate is not 4, 10 or 21, VAT on a foreign kind, an `eu-services` client without a non-Spanish EU prefix and a `non-eu-services` client with an EU prefix.
- 303: `eu-services` base in [59], `non-eu-services` base in [120] (information boxes, no VAT accrued). Source: AEAT Pre303 2026 note on additional information.
- 390: the same rows in [103] and [110]; [108] = [99] + [103] + [110] (390 instructions 2025, box 108 formula, other terms not used).
- 349 unchanged: it already takes issued rows to EU clients without VAT as key S.

## Impact

`register.py`, `aeat303.py`, `aeat390.py`, SKILL.md, tests. Not covered: corrective invoices (Roadmap #49), OSS ([123]/[124], [126]/[127]). Byte-for-byte check of [59]/[120] and [103]/[110]/[108] still waits for AEAT golden files.
