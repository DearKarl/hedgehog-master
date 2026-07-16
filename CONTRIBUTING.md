# Contributing to Hedgehog Master

Thank you for helping build a rigorous, local-first presentation harness for research and technical communication.

## Project Direction

Hedgehog Master accepts contributions that improve one or more of these goals:

- formal academic and technical communication;
- editable PowerPoint output;
- deterministic scientific diagrams;
- source traceability and citation retention;
- local project workflows;
- reliable SVG and PPTX validation;
- accessible, publication-oriented visual design.

Public documentation, issue descriptions, pull requests, and example content must be written in English.

## Development Setup

### Requirements

- Python 3.10 or newer
- Git
- Node.js and pnpm when working on `packages/diagram-ir`

### Clone and Install

```bash
git clone https://github.com/DearKarl/hedgehog-master.git
cd hedgehog-master

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For Diagram IR development:

```bash
cd packages/diagram-ir
pnpm install
pnpm check
```

## Before Opening a Pull Request

1. Open an issue before broad workflow, prompt, schema, or architecture changes.
2. Keep each pull request focused on one behavior or one coherent documentation change.
3. Explain the problem, the chosen approach, and the validation performed.
4. Review AI-assisted changes yourself. The contributor remains responsible for every claim and line in the submission.
5. Preserve license notices and source attribution.
6. Do not mix unrelated formatting or generated-artifact churn into the patch.

## Validation

Run checks that match the affected area.

### Python

```bash
python -m compileall skills/hedgehog-master/scripts
```

### Diagram IR

```bash
cd packages/diagram-ir
pnpm check
```

### SVG Projects

```bash
python skills/hedgehog-master/scripts/project_manager.py validate projects/<project-name>
python skills/hedgehog-master/scripts/svg_quality_checker.py projects/<project-name>
```

### Documentation

- Check relative links.
- Keep public prose in English.
- Distinguish current behavior from roadmap items.
- Do not claim publication readiness without the relevant validation evidence.

## Contribution Areas

Welcome contributions include:

- Diagram IR schemas, layouts, compilers, and tests
- academic flowchart and system-diagram profiles
- source conversion fidelity
- citation and claim-traceability tooling
- SVG and PPTX export correctness
- local review and editing interfaces
- accessible color, typography, and print validation
- focused bug fixes with reproducible cases

Changes that require prior discussion include:

- renaming compatibility-sensitive internal paths;
- replacing the project workflow model;
- adding mandatory package managers or deployment platforms;
- weakening validation or provenance requirements;
- introducing a hosted service that uploads local source material by default.

## Reporting Bugs

Open an issue at [GitHub Issues](https://github.com/DearKarl/hedgehog-master/issues) and include:

- operating system and Python version;
- the command or agent request used;
- minimal reproduction material when it can be shared;
- expected and actual behavior;
- relevant logs with secrets removed.

## Code of Conduct

Participation is governed by the [Code of Conduct](./CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contribution is licensed under the repository's [MIT License](./LICENSE). Third-party material must remain compatible with that license and retain its required notices.
