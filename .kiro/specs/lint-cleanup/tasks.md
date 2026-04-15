# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Lint Falha Sem Supressão
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the violations exist
  - **Scoped PBT Approach**: Scope the property to the concrete failing files identified in the design
  - Run `flake8 src/ --max-line-length=120` (without `--extend-ignore`) on UNFIXED code
  - Confirm violations are reported for each affected file:
    - `purchase_router.py:1: F401 'fastapi.FastAPI' imported but unused`
    - `test_worker_logs.py: E741 ambiguous variable name 'l'`
    - `test_webapi_logs.py: E741 ambiguous variable name 'l'`
    - `conftest.py: F811 redefinition of unused 'trace'`
    - `worker.py: F841 local variable 'purchase_id' is assigned to but never used`
    - `program.py: E402 module level import not at top of file`
    - `db.py: W291/W293 trailing whitespace`
    - `file_service.py: E302 expected 2 blank lines`
    - `nfce_extractor.py: W391/W292`
  - Document all counterexamples found (exact flake8 output lines)
  - **EXPECTED OUTCOME**: `flake8` exits with non-zero code (this is correct - it proves the bug exists)
  - Mark task complete when test is run and failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Comportamento de Runtime Inalterado
  - **IMPORTANT**: Follow observation-first methodology
  - Run `pytest src/tests/` on UNFIXED code and record which tests pass
  - Observe: `test_worker_logs.py` tests pass on unfixed code (log field assertions)
  - Observe: `test_webapi_logs.py` tests pass on unfixed code (HTTP log field assertions)
  - Observe: `conftest.py` fixtures work correctly on unfixed code
  - The existing hypothesis-based tests in `test_worker_logs.py` and `test_webapi_logs.py` ARE the preservation property tests — they cover the full input domain via property-based testing
  - Verify ALL existing tests pass on UNFIXED code before proceeding
  - **EXPECTED OUTCOME**: `pytest src/tests/` exits with code 0 (confirms baseline behavior to preserve)
  - Mark task complete when tests are run and all pass on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix lint violations across all affected files

  - [x] 3.1 Fix F401 — remove unused imports
    - `src/webapi/routers/purchase_router.py`: change `from fastapi import FastAPI, APIRouter` → `from fastapi import APIRouter`
    - `src/tests/test_worker_logs.py`: remove `import pytest`, `from unittest.mock import patch, MagicMock`
    - `src/tests/test_webapi_logs.py`: remove `import pytest`, `from unittest.mock import patch, MagicMock`
    - _Bug_Condition: isBugCondition(file, line) where hasUnusedImport(file, line) is True_
    - _Expected_Behavior: flake8 reports zero F401 errors after fix_
    - _Preservation: no runtime behavior changes — unused imports have no effect on execution_
    - _Requirements: 2.2_

  - [x] 3.2 Fix E741 — rename ambiguous variable `l` to `line`
    - `src/tests/test_worker_logs.py`: in `_parse_all_logs`, rename `l` → `line` in the list comprehension
    - `src/tests/test_webapi_logs.py`: in `_parse_all_logs`, rename `l` → `line` in the list comprehension
    - _Bug_Condition: isBugCondition(file, line) where hasAmbiguousVariableName(file, line) is True_
    - _Expected_Behavior: flake8 reports zero E741 errors after fix_
    - _Preservation: list comprehension result is identical — only variable name changes_
    - _Requirements: 2.6_

  - [x] 3.3 Fix F811 — remove duplicate import of `trace` in conftest.py
    - `src/tests/conftest.py`: the `from opentelemetry import trace` at the bottom is redundant — remove it; the shim block at the top already makes `trace` available via the explicit import in the fixtures section
    - _Bug_Condition: isBugCondition(file, line) where hasRedefinedUnusedName(file, line) is True_
    - _Expected_Behavior: flake8 reports zero F811 errors after fix_
    - _Preservation: fixtures continue to work — `trace` is still imported once_
    - _Requirements: 2.3_

  - [x] 3.4 Fix F841 — remove or use unused variable `purchase_id` in worker.py
    - `src/worker_app/worker.py`: `purchase_id = purchase_service.process(db, receipt.purchase)` — the variable IS used in the `logger.info` call below; verify flake8 is reporting this correctly; if flake8 still flags it, inline the call or confirm the usage is recognized
    - _Bug_Condition: isBugCondition(file, line) where hasUnusedVariable(file, line) is True_
    - _Expected_Behavior: flake8 reports zero F841 errors after fix_
    - _Preservation: logger.info continues to receive the correct purchase_id value_
    - _Requirements: 2.4_

  - [x] 3.5 Fix E402 — add `# noqa: E402` for justified out-of-order imports
    - `src/config/otel_config.py`: add `# noqa: E402` to the line `from config.log_config import configure_logging` inside `configure_otel` — intentional to avoid circular import
    - `src/worker_app/program.py`: add `# noqa: E402` to all import lines that follow `configure_otel("worker_app")` — intentional to ensure OTel is initialized before other modules load
    - _Bug_Condition: isBugCondition(file, line) where hasModuleLevelImportNotAtTop(file, line) is True_
    - _Expected_Behavior: flake8 reports zero E402 errors after fix_
    - _Preservation: OTel initialization order is preserved; no circular import introduced_
    - _Requirements: 2.5_

  - [x] 3.6 Fix W291/W293 — remove trailing whitespace
    - `src/database/db.py`: remove trailing spaces on lines with `global __db `, `return __db `, and any other affected lines
    - `src/entities/entitity.py`: remove trailing spaces on all affected lines
    - `src/services/file_service.py`: remove trailing spaces on all affected lines
    - _Bug_Condition: isBugCondition(file, line) where hasTrailingWhitespace(file, line) is True_
    - _Expected_Behavior: flake8 reports zero W291/W293 errors after fix_
    - _Preservation: pure whitespace change — no runtime effect_
    - _Requirements: 2.7_

  - [x] 3.7 Fix W292/W391 — fix end-of-file newlines
    - `src/services/nfce_extractor.py`: ensure file ends with exactly one newline (no blank line at EOF)
    - `src/webapi/schemas/line_of_business_schema.py`: ensure file ends with exactly one newline; remove leading blank line if present
    - _Bug_Condition: isBugCondition(file) where hasMissingNewlineAtEOF(file) OR hasBlankLineAtEOF(file) is True_
    - _Expected_Behavior: flake8 reports zero W292/W391 errors after fix_
    - _Preservation: pure whitespace change — no runtime effect_
    - _Requirements: 2.8_

  - [x] 3.8 Fix E302 — add missing blank lines between top-level definitions
    - `src/services/file_service.py`: add a blank line between `move_to_processed` and `get_file_path` so there are 2 blank lines separating them
    - `src/services/nfce_extractor.py`: verify 2 blank lines before `extract_nfce_data` if any other top-level definition precedes it
    - `src/config/log_config.py`: add 2 blank lines between top-level function/class definitions where E302 is reported
    - `src/webapi/routers/company_router.py`: add 2 blank lines between route handler functions where E302 is reported
    - _Bug_Condition: isBugCondition(file, line) where hasInsufficientBlankLinesBetweenDefs(file, line) is True_
    - _Expected_Behavior: flake8 reports zero E302 errors after fix_
    - _Preservation: pure formatting change — no runtime effect_
    - _Requirements: 2.9_

  - [x] 3.9 Remove `--extend-ignore` from CI
    - `.github/workflows/ci.yaml`: change the flake8 lint step from `flake8 src/ --max-line-length=120 --extend-ignore=E302,E203,E402,E741,W291,W292,W293,W391,F401,F811,F841` to `flake8 src/ --max-line-length=120`
    - _Bug_Condition: CI suppresses lint violations via --extend-ignore_
    - _Expected_Behavior: CI runs flake8 without any --extend-ignore flag_
    - _Preservation: --max-line-length=120 remains unchanged (Requirement 3.4)_
    - _Requirements: 2.1_

  - [x] 3.10 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Lint Passa Sem Supressão
    - **IMPORTANT**: Re-run the SAME check from task 1 - do NOT write a new test
    - Run `flake8 src/ --max-line-length=120` (without `--extend-ignore`) on FIXED code
    - **EXPECTED OUTCOME**: `flake8` exits with code 0, zero violations reported (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

  - [x] 3.11 Verify preservation tests still pass
    - **Property 2: Preservation** - Comportamento de Runtime Inalterado
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run `pytest src/tests/` on FIXED code
    - **EXPECTED OUTCOME**: All tests pass (confirms no regressions)
    - Confirm hypothesis-based tests in `test_worker_logs.py` and `test_webapi_logs.py` still pass
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run `flake8 src/ --max-line-length=120` — must exit with code 0
  - Run `pytest src/tests/` — all tests must pass
  - Confirm CI yaml no longer contains `--extend-ignore`
  - Ask the user if any questions arise.
