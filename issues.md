# Lab 5 — Static Code Analysis Issue Log

## Findings and fixes

| Issue | Type / severity | Original location | Description | Fix applied |
|---|---|---|---|---|
| Unsafe YAML loader | Security / medium | `loadConfig` | The generic YAML loader can construct Python objects from untrusted YAML. | Replaced it with `yaml.safe_load` and validated the configuration shape. |
| Hardcoded database password | Security / low | `connectWardenDb` | A credential was embedded in source code. | Read connection settings from environment variables and never return the password. |
| Flask debug mode | Security / high | `runPortal` | Debug mode can expose the interactive debugger. | Disabled debug mode and bound the development server to localhost. |
| Insecure logging listener | Security / medium | `startRemoteLogConfig` | Remote logging configuration can allow unsafe configuration changes. | Disabled the remote listener. |
| Weak random source for lottery | Security / low | `roomLottery` | The standard pseudo-random generator is not intended for security-sensitive use. | Used `secrets.SystemRandom` for the lottery ordering. |
| Mutable default argument | Correctness | `allocateRoom` | A shared default list can carry state across calls. | Replaced the list default with `None`. |
| Capacity check | Correctness | `allocateRoom` | The original condition allowed a full room to accept another occupant. | Reject rooms when occupant count is greater than or equal to capacity. |
| Gender compatibility | Correctness | `allocateRoom` | The original function did not enforce the block's configured gender. | Check the room gender before allocation. |
| Duplicate allocation | Correctness | `allocateRoom` | A student could be assigned more than once. | Return the existing room for an already allocated student. |
| Vacating a room | Correctness | `vacateRoom` | Removing an allocation did not remove the student from the room occupant list. | Update both the allocation dictionary and occupant list. |
| Vacant bed count | Correctness | `vacantBeds` | The original function counted beds only in completely empty rooms. | Sum the unused capacity in every room. |
| HTML injection | Security | `roomLookup` | Query-string input was concatenated into HTML without escaping. | Escape the student identifier and allocation text. |
| Style and naming | Style | Multiple functions | Unused imports, camelCase names, missing docstrings, and long lines reduced maintainability. | Removed unused imports, used snake_case, added docstrings, and reformatted long lines. |

## Verification

- Pylint after-fix report: 10.00/10.
- Bandit after-fix report: no issues identified.
- Flake8 after-fix report: empty (no violations reported).
- The original source and baseline reports are preserved in `hostel_allocation_original.py` and `reports/before/`.
