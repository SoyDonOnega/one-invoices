# Monthly routine (template)

Schedule: `0 20 28-31 * *` (local time). Replace `<…>` with your paths. Prompt:

---

Monthly invoice routine. Skill: `~/.claude/skills/one-invoices/SKILL.md`, section "Automatic mode". The user chose that invoices are registered without confirming each one; the skill's automatic mode encodes that.

0. **Gate.** Run `date -v+1d +%d` (macOS; `date -d tomorrow +%d` on Linux). If it is not `01`, end with "Not the end of the month." Check that the Drive client runs; if not, end with "Drive is not running: nothing done."
1. **Paths.** Config: `~/.claude/skill-data/one-invoices/config.json`. Mailbox to the assistant (append-only): `<path to To-Assistant.md>`. State: `~/.claude/scheduled-tasks/<task id>/state.json`.
2. **Register.** Run `auto-register` over the PDFs in `shared_inbox`.
3. **Filing month?** If tomorrow's month is 1, 4, 7 or 10: list the closing quarter's register rows and totals, and write `state.json` = `{"pending": {"year": Y, "quarter": Q, "annual": <true in January>, "asked": "<today>"}}`.
4. **Message.** Append one entry to the mailbox: in a filing month, a question with the quarter's invoices and totals ending "Anything missing? When everything is in, answer 'generate'", plus one line asking the assistant to relay it and to write a notice `About: invoices: generate` quoting the answer. Otherwise a notice only if something was registered or left in the inbox.
5. **Report.** Registered, left in the inbox and why, question sent or not.

Rules: never file, sign or send anything; never generate the files here; writes limited to what automatic mode writes, `state.json` and one mailbox append.
