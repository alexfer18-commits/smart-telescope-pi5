# Hardware inventory (as of 2026-11-08)

Durable state of the physical build. Everything here is a fact about the bench,
not a plan. If this file and `hardware/BOM.md` disagree, the BOM is wrong.

## In possession

| Item | Qty | Notes |
|---|---|---|
| Raspberry Pi 5, 8 GB | 1 | — |
| NEMA 17 17HS4401 | **2** | 1.8°/step, 1.7 A/phase, 40 N·cm. One per axis: #1 azimuth, #2 altitude. Verify both are the same model before mounting. |

## Remaining BOM

| Scenario | USD |
|---|---|
| To buy, no Hailo | **168** |
| To buy, with Hailo-8L | **238** |
| Instrument total, including the hardware already owned ($110) | 278 / 348 |

## Critical path

**$70 = Pi Camera 3 ($25) + 12 V PSU ($15) + 2020 aluminium ($30).**

The two A4988 and the 5 V buck ($18) are also required to energise the system,
but they are local-stock items and are not the lead-time risk.

## Where this lives

- `hardware/BOM.md` — priced line items with supplier links.
- `hardware/SHOPPING_LIST.md` — purchase order and arrival sequence.
- `hardware/ASSEMBLY_GUIDE.md` §1.4 — which motor drives which axis, with the
  torque check per axis.
- `docs/mechanical_analysis.md` — why azimuth needs nothing and altitude needs
  balance.

## Arithmetic note

The figure "$110 / $180" circulates in conversation and is wrong for this BOM:
$110 is what is *already owned*, not what is left to buy. The previous revision
of the BOM had the second NEMA 17 as a purchase line, so marking both motors as
owned moves $15 from "to buy" to "owned" — the instrument total ($278) does not
change, because both motors were always in it.
