# Spec Delta

## ADDED Requirements

### Requirement: Carry-forward from earlier quarters
Box [110] SHALL be the negative results of earlier quarters still pending, computed from the register; [78] the part applied in this quarter, at most the positive result before it; [87] = [110] − [78]. The user SHALL be able to override [110] with `--carry <amount>`.

#### Scenario: Negative quarter followed by a positive one
- **WHEN** Q4 2026 ends at −300.00 and Q1 2027 has a result of 500.00 before carry-forward
- **THEN** Q1 2027 has [110] 300.00, [78] 300.00, [87] 0.00 and [71] 200.00

#### Scenario: Gap in the register
- **WHEN** an earlier quarter of the chain has no register rows and no result can be computed
- **THEN** the tool asks for `--carry`
