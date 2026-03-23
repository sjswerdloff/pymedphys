### Issue: Fix bandit security scan format error

**Description:**
The current setup for the bandit security scan in the CI workflow is producing a format error due to the use of the SARIF format, which is not being parsed correctly. This has been causing the security workflow to fail.

**Error Message:**
```
Error: Invalid format for Bandit security scan results. Expected valid JSON format.
```

**Suggested Solution:**
To resolve this issue, the output format of the bandit scan should be changed from SARIF to JSON. This can be accomplished by adjusting the command in the workflow file to include the appropriate format flag:

```bash
bandit -f json -o bandit_output.json
```

This adjustment will ensure that the output file is in a valid format that can be correctly processed by our CI tooling.

**Next Steps:**
1. Update the CI workflow script to use JSON format for the bandit scan output.
2. Test the workflow to confirm that the issue is resolved.
3. Monitor future runs for similar errors to ensure the fix is effective.

**Priority:** Medium

---

Please investigate and implement this change as soon as possible to avoid disruptions in the CI pipeline.