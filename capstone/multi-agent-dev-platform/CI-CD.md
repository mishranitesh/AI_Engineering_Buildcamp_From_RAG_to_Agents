# CI/CD for running unit tests, evaluations, and/or deployment

- Create `.github/workflows/tests.yml` in the repo root (not inside multi-agent-dev-platform/)

Two things to do after creating this file:

1. Add secrets in GitHub:

- Go to your repo → Settings → Secrets and variables → Actions
- Add OPENAI_API_KEY (needed for KB tests)
- Add GH_TOKEN (your GitHub token — note: GITHUB_TOKEN is reserved by GitHub Actions)

2. Note: test_knowledge_base.py and test_tools_mocked.py are excluded from CI for now since ChromaDB needs the seeded knowledge_db/ to exist. Only the pure unit tests run in CI.

Once you push this file, GitHub Actions will automatically run on every push to the capstone directory.

## Testing

Push the workflow file to GitHub — that triggers it automatically:

```
git add .github/workflows/tests.yml
git commit -m "Add CI/CD: unit tests on push"
git push
```

Then go to your GitHub repo → "Actions" tab — you'll see the workflow running in real time.

## Testing locally using act:

```
# Install act (runs GitHub Actions locally)
brew install act

# Run the workflow locally
cd AI_Engineering_Buildcamp_From_RAG_to_Agents
act push --job test --container-architecture linux/amd64
# The --container-architecture linux/amd64 flag is needed for Apple M-series chips as the warning suggests.

# Output
(.venv) niteshmishra@Mac AI_Engineering_Buildcamp_From_RAG_to_Agents % act push --job test --container-architecture linux/amd64
INFO[0000] Using docker host 'unix:///var/run/docker.sock', and daemon socket 'unix:///var/run/docker.sock'
[Unit Tests/test] ⭐ Run Set up job
[Unit Tests/test] 🚀  Start image=catthehacker/ubuntu:act-latest
[Unit Tests/test]   🐳  docker pull image=catthehacker/ubuntu:act-latest platform=linux/amd64 username= forcePull=true
[Unit Tests/test]   🐳  docker create image=catthehacker/ubuntu:act-latest platform=linux/amd64 entrypoint=["tail" "-f" "/dev/null"] cmd=[] network="host"
[Unit Tests/test]   🐳  docker run image=catthehacker/ubuntu:act-latest platform=linux/amd64 entrypoint=["tail" "-f" "/dev/null"] cmd=[] network="host"
[Unit Tests/test]   🐳  docker exec cmd=[node --no-warnings -e console.log(process.execPath)] user= workdir=
[Unit Tests/test]   ✅  Success - Set up job
[Unit Tests/test]   ☁  git clone 'https://github.com/actions/setup-python' # ref=v5
[Unit Tests/test] ⭐ Run Main actions/checkout@v4
[Unit Tests/test]   🐳  docker cp src=/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/. dst=/Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents
[Unit Tests/test]   ✅  Success - Main actions/checkout@v4 [1.776263875s]
[Unit Tests/test] ⭐ Run Main actions/setup-python@v5
[Unit Tests/test]   🐳  docker cp src=/Users/niteshmishra/.cache/act/actions-setup-python@v5/ dst=/var/run/act/actions/actions-setup-python@v5/
[Unit Tests/test]   🐳  docker exec cmd=[/opt/acttoolcache/node/24.16.0/x64/bin/node /var/run/act/actions/actions-setup-python@v5/dist/setup/index.js] user= workdir=
[Unit Tests/test]   ❓  ::group::Installed versions
| (node:31) [DEP0040] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
| (Use `node --trace-deprecation ...` to show where the warning was created)
| Successfully set up CPython (3.11.15)
[Unit Tests/test]   ❓  ::endgroup::
[Unit Tests/test]   ❓ add-matcher /run/act/actions/actions-setup-python@v5/.github/python.json
[Unit Tests/test]   ✅  Success - Main actions/setup-python@v5 [2.089405625s]
[Unit Tests/test]   ⚙  ::set-env:: PKG_CONFIG_PATH=/opt/hostedtoolcache/Python/3.11.15/x64/lib/pkgconfig
[Unit Tests/test]   ⚙  ::set-env:: Python_ROOT_DIR=/opt/hostedtoolcache/Python/3.11.15/x64
[Unit Tests/test]   ⚙  ::set-env:: Python2_ROOT_DIR=/opt/hostedtoolcache/Python/3.11.15/x64
[Unit Tests/test]   ⚙  ::set-env:: Python3_ROOT_DIR=/opt/hostedtoolcache/Python/3.11.15/x64
[Unit Tests/test]   ⚙  ::set-env:: LD_LIBRARY_PATH=/opt/hostedtoolcache/Python/3.11.15/x64/lib
[Unit Tests/test]   ⚙  ::set-env:: pythonLocation=/opt/hostedtoolcache/Python/3.11.15/x64
[Unit Tests/test]   ⚙  ::set-output:: python-version=3.11.15
[Unit Tests/test]   ⚙  ::set-output:: python-path=/opt/hostedtoolcache/Python/3.11.15/x64/bin/python
[Unit Tests/test]   ⚙  ::add-path:: /opt/hostedtoolcache/Python/3.11.15/x64
[Unit Tests/test]   ⚙  ::add-path:: /opt/hostedtoolcache/Python/3.11.15/x64/bin
[Unit Tests/test] ⭐ Run Main Install uv
[Unit Tests/test]   🐳  docker exec cmd=[bash -e /var/run/act/workflow/2] user= workdir=capstone/multi-agent-dev-platform
| Requirement already satisfied: uv in /opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages (0.11.19)
| WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.
[Unit Tests/test]   ✅  Success - Main Install uv [1.259373833s]
[Unit Tests/test] ⭐ Run Main Install dependencies
[Unit Tests/test]   🐳  docker exec cmd=[bash -e /var/run/act/workflow/3] user= workdir=capstone/multi-agent-dev-platform
| Using Python 3.11.15 environment at: /opt/hostedtoolcache/Python/3.11.15/x64
| Checked 14 packages in 231ms
[Unit Tests/test]   ✅  Success - Main Install dependencies [494.006708ms]
[Unit Tests/test] ⭐ Run Main Run unit tests
[Unit Tests/test]   🐳  docker exec cmd=[bash -e /var/run/act/workflow/4] user= workdir=capstone/multi-agent-dev-platform
| Using Python 3.11.15 environment at: /opt/hostedtoolcache/Python/3.11.15/x64
| Checked 1 package in 47ms
| ============================= test session starts ==============================
| platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0 -- /opt/hostedtoolcache/Python/3.11.15/x64/bin/python
| cachedir: .pytest_cache
| rootdir: /Users/niteshmishra/AI/new/AI_Engineering_Buildcamp_From_RAG_to_Agents/capstone/multi-agent-dev-platform
| configfile: pyproject.toml
| plugins: anyio-4.13.0
collected 23 items
|
| tests/test_parsers.py::test_extract_code_files_single_file PASSED        [  4%]
| tests/test_parsers.py::test_extract_code_files_multiple_files PASSED     [  8%]
| tests/test_parsers.py::test_extract_code_files_empty_input PASSED        [ 13%]
| tests/test_parsers.py::test_extract_code_files_no_match PASSED           [ 17%]
| tests/test_parsers.py::test_extract_code_files_language_agnostic PASSED  [ 21%]
| tests/test_parsers.py::test_parse_review_comments_splits_numbered_items PASSED [ 26%]
| tests/test_parsers.py::test_parse_review_comments_preserves_content PASSED [ 30%]
| tests/test_parsers.py::test_parse_review_comments_fallback_on_no_match PASSED [ 34%]
| tests/test_parsers.py::test_parse_review_comments_filters_short_items PASSED [ 39%]
| tests/test_parsers.py::test_extract_user_stories_picks_as_a_format PASSED [ 43%]
| tests/test_parsers.py::test_extract_user_stories_caps_at_eight PASSED    [ 47%]
| tests/test_parsers.py::test_extract_user_stories_fallback PASSED         [ 52%]
| tests/test_state.py::test_workflow_state_defaults PASSED                 [ 56%]
| tests/test_state.py::test_workflow_state_stores_requirement PASSED       [ 60%]
| tests/test_state.py::test_workflow_state_jira_fields PASSED              [ 65%]
| tests/test_state.py::test_workflow_state_pr_phase_transitions PASSED     [ 69%]
| tests/test_generators.py::test_write_backend_files_creates_files PASSED  [ 73%]
| tests/test_generators.py::test_write_backend_files_correct_content PASSED [ 78%]
| tests/test_generators.py::test_write_tests_creates_test_dir PASSED       [ 82%]
| tests/test_generators.py::test_write_architecture_creates_files PASSED   [ 86%]
| tests/test_generators.py::test_write_review_joins_comments PASSED        [ 91%]
| tests/test_generators.py::test_write_readme PASSED                       [ 95%]
| tests/test_generators.py::test_create_zip_produces_file PASSED           [100%]
|
| =============================== warnings summary ===============================
| ../../../../../../../opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/opentelemetry/util/_importlib_metadata.py:32
|   /opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/opentelemetry/util/_importlib_metadata.py:32: DeprecationWarning: SelectableGroups dict interface is deprecated. Use select.
|     return EntryPoints(ep for group_eps in eps.values() for ep in group_eps)
|
| -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
| ======================== 23 passed, 1 warning in 3.05s =========================
[Unit Tests/test]   ✅  Success - Main Run unit tests [3.969688291s]
[Unit Tests/test] ⭐ Run Post actions/setup-python@v5
[Unit Tests/test]   🐳  docker exec cmd=[/opt/acttoolcache/node/24.16.0/x64/bin/node /var/run/act/actions/actions-setup-python@v5/dist/cache-save/index.js] user= workdir=
| (node:105) [DEP0040] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
| (Use `node --trace-deprecation ...` to show where the warning was created)
[Unit Tests/test]   ✅  Success - Post actions/setup-python@v5 [628.396667ms]
[Unit Tests/test] ⭐ Run Complete job
[Unit Tests/test] Cleaning up container for job test
[Unit Tests/test]   ✅  Success - Complete job
[Unit Tests/test] 🏁  Job succeeded
```

What to check after pushing:

| Status | Meaning |
|---------|---------|
| 🟡 Yellow circle | Running |
| ✅ Green checkmark | All tests passed |
| ❌ Red X | Tests failed — click to see logs |

If it fails, click the job name → expand the failing step to see the exact error.




