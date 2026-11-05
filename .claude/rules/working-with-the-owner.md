# Working with the owner

These rules cover how Claude works with the site's owner. They apply to every task in this repository, including scheduled runs.

## Starting a task

- Read `CLAUDE.md` and the rule files first. Earlier decisions are recorded there; follow them rather than proposing something that was already decided. If a request conflicts with a recorded rule, say so and ask instead of overriding it.
- Rule files with `paths` load only when a matching file is opened. Before planning a change in a directory, read its rule file (the map is in `CLAUDE.md`).
- Write the completion criteria (the conditions under which the task counts as done) at the start of the task. Rewrite them if the scope changes. Do not treat the task as finished until they are met.
- If a request can be read more than one way, start on the most likely reading and say which one you chose.

## Asking questions

- Put questions for the owner in the owner's Q&A table, a claude.ai artifact named "Thesis 質問箱" (find it with the Artifact tool's `list` action; write rows with ArtifactData, collection `questions`). Do not leave questions waiting in the chat.
- Never ask what is already decided. Before adding a question, read every row of the Q&A table (answered and applied ones too), the rule files, the shared decision files and project memory; if the answer is there, follow it. If an earlier answer must be reopened, say in `context` where it is and why.
- One decision per question, in one short sentence, with one recommended answer. Put explanations in the row's `context`, not in the question.
- If the session cannot reach the Q&A table, ask in the chat in the same short form.

## Reporting

- Talk to the owner in Japanese, in plain, short sentences. Explain technical terms. (Repository contents stay in English; see `english-first.md`.)
- Do not use emoji.
- A report gives the pull request link, what changed, and what stayed the same and why.
- End every report with three parts: Problems / What I checked / What I could not check (for example, that the live site cannot be opened from the sandbox), and leave one line in the execution log.
- When asked which questions are still open, reply with the link to the Q&A table and the number of open rows; do not list them in the chat.
