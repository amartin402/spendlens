# AGENTS.md

- Make focused, regular commits and explain decisions in the commit messages.
- Read product-spec.md before changing behavior.
- All money is integer cents. Never use floats for money.
- All frontend backend calls go through frontend/src/services/.
- Every backend query must be scoped by user_id.
- Run `make test` before declaring a task done.
- Never commit secrets. Use environment variables.
- Every time there is a milestone change to the development add it to the docs/ai-workflow.md file(## Step log). Any work you get wrong add a note to ## Things the AI got wrong (and how I fixed them).s 