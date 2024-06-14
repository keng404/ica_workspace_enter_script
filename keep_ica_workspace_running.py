import re
from playwright.sync_api import Playwright, sync_playwright, expect
from pprint import pprint
import requests
from requests.structures import CaseInsensitiveDict
import json
import os
import argparse
import base64
import sys
import time 
### Use assertion to throw error if URL cannot be loaded or found (i.e. sends a 400 or 500 response)
def handle_response(response):
    assert (response.status < 400 and response.status >= 200) or response.status == 500, f"URL visited: {response.url}  Status code: {response.status} >= 400"

# STEP 1: generate psToken from username and password
def generate_ps_token(auth_object):
    api_base_url = os.environ['ICA_ROOT_URL'] +"/ica/rest"
    endpoint = f"/api/tokens?tenant={auth_object['domain_name']}"
    credentials = base64.b64encode(bytes(f"{auth_object['username']}:{auth_object['password']}", "utf-8")).decode()
    full_url = api_base_url + endpoint
    headers = CaseInsensitiveDict()
    headers['accept'] = "application/vnd.illumina.v3+json"
    headers['Authorization'] = f"Basic {credentials}"
    headers['Content-Type'] = "application/vnd.illumina.v3+json"
    token = None
    try:
        platform_response = requests.post(full_url, headers=headers)
        token = platform_response.json()['token']
    except:
        pprint(platform_response,indent=4)
        raise ValueError(f"Could not generate psToken for the following URL: https://{auth_object['domain_name']}.login.illumina.com")
    return token 
## STEP 2, log into ICA, navigate to project, Bench -> Workspaces, identify workspace of interest and enter it.
def enter_workspace(playwright: Playwright,auth_object,headless_mode) -> None:
    browser = playwright.chromium.launch(headless=headless_mode)
    context = browser.new_context()
    context.grant_permissions(["clipboard-read"])
    context.grant_permissions(["clipboard-write"])
    page = context.new_page()
    # sign into domain --- platform home
    #page.on("response", handle_response)
    print(f"Logging into {auth_object['domain_name']} domain")
    page.goto(f"https://platform.login.illumina.com/platform-services-manager/?rURL=https://{auth_object['domain_name']}.login.illumina.com/platform-home/&redirectMethod=GET&clientId=ps-home")
    page.locator("#login").click()
    page.locator("#login").fill(f"{auth_object['username']}")
    page.locator("#login").press("Tab")
    page.locator("input[name=\"password\"]").fill(f"{auth_object['password']}")
    page.get_by_role("button", name="Sign In").click()
    # click on ICA card
    print(f"Entering into ICA")
    page.get_by_role("link", name="Illumina Connected Analytics", exact=True).click()
    page.get_by_text("Cookies", exact=True).click()
    page.get_by_role("button", name="Accept and close").click()

    #page.goto(f"{os.environ['ICA_ROOT_URL']}/ica/projects")

    # enter into project context
    print(f"Entering into the ICA project {auth_object['project_name']}")
    ## by project id
    if auth_object['project_id'] is not None:
        #page.on("response", handle_response)
        page.goto(f"{os.environ['ICA_ROOT_URL']}/ica/projects/{auth_object['project_id']}")
    else:
        page.locator("#btn-cardstack-table").click()
        time.sleep(1)
        page.wait_for_load_state() # the promise resolves after "load" event.
        found_project = page.get_by_role("cell", name=f"{auth_object['project_name']}",exact=True).locator("div").count() > 0
        if found_project is True:
            page.get_by_role("cell", name=f"{auth_object['project_name']}").locator("div").dblclick()
            ## Grabbing project URN from project details tab
            print(f"Grabbing project URN {auth_object['project_name']} to get project id")
            page.get_by_role("button", name="Project Settings").click()
            page.get_by_role("link", name="Details").click()
            page.get_by_label("URN").click(click_count=3)
            ### only valid for MacOs -- need to adapt for windows
            page.get_by_label("URN").press("Meta+c")
            project_urn = page.evaluate("navigator.clipboard.readText()")
            if project_urn != "":
                print(f"Found project URN {project_urn}")
                project_urn_split = project_urn.split(':')
                project_metadata_split = project_urn_split[len(project_urn_split)-1].split("#")
                auth_object['project_id'] = project_metadata_split[0]
            else:
                raise ValueError(f"Could not get Project URN for project {auth_object['project_name']}")
        else:
            raise ValueError(f"Could not find the project: {auth_object['project_name']}")
    ### enter workspaces of project
    #page.on("response", handle_response)
    page.goto(f"{os.environ['ICA_ROOT_URL']}/ica/projects/{auth_object['project_id']}/workspaces")
    page.locator("#cardstackandmasterdetaillayout-toggle-TABLE").get_by_role("button").click()
    time.sleep(1)
    found_workspace = page.get_by_role("cell",name=f"{auth_object['workspace_name']}",exact=True).count() > 0
    if found_workspace is True:
        page.get_by_role("cell",name=f"{auth_object['workspace_name']}",exact=True).click(click_count=2)
        page.get_by_label("Details").get_by_text("Details").click(click_count=2)
        page.get_by_label("Status").click(click_count=2)
        ### only valid for MacOs -- need to adapt for windows
        page.locator(".v-panel-content").press("Meta+c")
        workspace_status = page.evaluate("navigator.clipboard.readText()")
        print(f"Workspace Name: {auth_object['workspace_name']} Status: {workspace_status}")
        if workspace_status == "Running":
            ## keep running workspace running
            page.get_by_role("button", name=" Back").click()
            page.get_by_role("button", name=" Keep running").click()
            print(f"Logged into running workspace {auth_object['workspace_name']}")
        elif workspace_status == "Stopped":
            ## keep re-start a stopped workspace
            time.sleep(1)
            page.get_by_role("button", name=" Start Workspace").click(click_count=3)
            time.sleep(3)
            page.get_by_role("button", name=" Back").click()
            print(f"Restarted workspace {auth_object['workspace_name']}\nYou may need to wait a few minutes before entering into it.")
        elif workspace_status == "Starting":
            print(f"Workspace {auth_object['workspace_name']} is still restarting\nYou may need to wait a few minutes before entering into it.")
        else:
            raise ValueError(f"Not sure what to do with workspace {auth_object['workspace_name']}.\nIt has status of {workspace_status}")
    else:
        raise ValueError(f"Could not find the workspace: {auth_object['workspace_name']} in the project {auth_object['project_id']}")
    # ---------------------
    ### sign out of ICA
    print(f"Logging out of ICA")
    page.locator("#btn-usermenu").click()
    page.get_by_role("option", name="Sign out").click()
    ### browser and admin steps
    context.clear_cookies()
    context.close()
    browser.close()
    return print(f"Finished work!")

#################################
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default=None,required=True, type=str, help="username [email] used to log into Connected Analytics")
    parser.add_argument('--password', default=None,required=True, type=str, help="password used to log into Connected Analytics")
    parser.add_argument('--domain_name', default=None,required=True, type=str, help="private domain name")
    parser.add_argument('--workspace_name', default=None,required=True, type=str, help="ICA workspace name")
    parser.add_argument('--project_id', default=None, type=str, help="[OPTIONAL] Connected Analytics project ID")
    parser.add_argument('--project_name', default=None, type=str, help="[OPTIONAL] Connected Analytics project Name to grab project ID")
    parser.add_argument('--ica_root_url', default="https://ica.illumina.com", type=str, help="ICA root url. In most use-cases, this option does not need to be configured")
    parser.add_argument('--interactive_mode',  action="store_false", help="run script in interactive mode")
    args, extras = parser.parse_known_args()
    #############
    auth_object = vars(args)
    os.environ['ICA_ROOT_URL'] = args.ica_root_url
    ############ script argument validation
    if auth_object['domain_name'] is None:
        raise ValueError("Private domain name [--domain_name <STR>] need to be provided")
    if auth_object['username'] is None or auth_object['password'] is None:
        raise ValueError("Both username [--username <STR>] and password [--password <STR>] need to be provided")
    if auth_object['project_id'] is None and auth_object['project_name'] is None:
        raise ValueError("Either project_id [--project_id <STR>] or project_name [--project_name <STR>] need to be provided")
    ######### Validate username + password combination
    ps_token = generate_ps_token(auth_object)
    if ps_token is None:
        raise ValueError("Username password combination is incorrect")
    else:
        ############ run automation to enter ICA workspace via playwright process
        with sync_playwright() as playwright:
            enter_workspace(playwright,auth_object,args.interactive_mode)
#################
if __name__ == '__main__':
    main()