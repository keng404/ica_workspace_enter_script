# Synopsis

Script will try to enter/re-start a workspace in Illumina Connected Analytics (ICA) programmatically.

This is demo code and should not be considered official code from Illumina.

Currently this allows for users to keep workspaces active (i.e. permanent workspaces) for their activity within ICA.

You can also try running the script in the docker image ```keng404/ica_workspace_enter_script:0.0.1```.

## Command line usage

``` bash
python3 keep_ica_workspace_running.py --domain_name {DOMAIN_NAME} --username {USERNAME} --password {PASSWORD} --project_name {ICA_PROJECT_NAME} --workspace_name {WORKSPACE_NAME} --interactive_mode
```

### Additional notes

- Only works on MacOS for now.
- Script will enter running workspace and re-start stopped workspace.
- ```interactive_mode``` mode flag can be toggled on/off --- this flag turns off headless mode, which is nice if you want to see how the script is navigating in the browser.
- No checks are done for invalid workspace names. You'll probably encounter a timeout error (30s) if script does not complete.
- Either ```project_name``` or ```project_id``` can be provided.
- Need to add ``` Ctrl + C ``` to get the copy-to-clipboard functionality in Linux and Windows OS.
  - Used in grabbing project URN and workspace status  

# install python modules

```bash
pip install -r requirements.txt
```

# Playwright setup on MacOS

## install and setup playwright

```bash
pip3 install playwright
echo "export PATH=$PATH:$HOME/Library/Python/{PYTHON_VERSION}/bin" >> ~/.bashrc
source ~/.bashrc
playwright install
```

## To perform codegen

```playwright codegen {URL_OF_INTEREST}```


## Playwright Documentation

```https://playwright.dev/python/docs/intro```
