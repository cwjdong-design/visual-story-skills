# Visual Story Skills

A standalone, Chinese-first production skill for **your own agent, accounts and creative canvas**. No original workbench, backend, database, vendor account or fixed model is required.

The skill extracts a comic production method: story development → production bible → storyboard → reference assets and generation planning → review and targeted rework. Short-drama instructions add timing, movement, audio and editing; this extension has not been validated through real end-to-end generation.

## Use

Import the entire `skills/visual-story-production/` directory into an agent that accepts directory-based skills. Otherwise explicitly ask your agent to read `SKILL.md` and its linked files. Exact installation and automatic discovery depend on the host agent; support for every agent is not claimed.

Example prompt:

> Use visual-story-production to turn this story into a six-panel comic. Prepare the story review, production bible and shot list first. Save a portable project. Do not start generation or publish anything yet.

Tool access, platform authentication and model credits must come from the user. No verified vendor-specific canvas adapter ships in v0.1.0. Without tools, the skill can still produce portable planning documents and prompts, but must not claim that media was generated.

## Validation

Python 3.10+, standard library only:

```sh
python -m unittest discover -s tests -v
python tools/check_package.py
python tools/build_release.py
```

Read the [Chinese guide](README.md) for the complete file map, examples and usage. The validator checks deterministic integrity, not creative quality or user approval. MIT licensed; third-party media rights are not included.
