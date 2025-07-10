# modules/controller_setup.py - The corrected version

from browser_use import Controller, ChatGoogle, ActionResult
from browser_use.browser import BrowserSession, BrowserProfile # Import BrowserProfile
from dotenv import load_dotenv
from utils import custom_actions
import os
from pathlib import Path



load_dotenv()

USER_DOWNLOADS_DIR = Path.home() / "Downloads"

# --- CONFIGURE THE AGENT'S COMPONENTS ---
llm = ChatGoogle(model='gemini-2.0-flash') 
controller = Controller() 


browser_profile = BrowserProfile(
    user_data_dir="~/.config/browseruse/profiles/default",
    downloads_path=str(USER_DOWNLOADS_DIR.resolve())
)

browser_session = BrowserSession(
    keep_alive=True,
    browser_profile=browser_profile
)

# --- REGISTER YOUR CUSTOM ACTIONS ---

@controller.action(
    "Pauses the script and waits for the user to manually complete an action in the browser, like logging in or solving a CAPTCHA. Call this when you are on a page that requires manual user intervention."
)
def pause_and_wait_for_user_action(reason: str) -> ActionResult:
    return custom_actions.pause_and_wait_for_user(reason)



@controller.action(
    "Clicks an element to open a file dialog and uploads a file in a single, atomic step. Provide the index of the element to click and the absolute path of the file."
)
async def click_and_upload_action(selector_index: int, file_path: str) -> ActionResult:
    
    return await custom_actions.click_and_upload(selector_index, file_path, browser_session)



@controller.action(
    "Waits for a file download to complete. This action must be called immediately AFTER clicking a download link or button."
)
async def download_file_action() -> ActionResult:
    return await custom_actions.download_file(browser_session)



@controller.action(
    "Saves the file that is currently being displayed directly in the browser (e.g., a PDF viewer). Use this when there is no download button."
)
async def save_displayed_file_action(filename: str) -> ActionResult:
    
    return await custom_actions.save_displayed_file(filename, browser_session, USER_DOWNLOADS_DIR)


@controller.action(
    "Checks if a given price string is a good deal by comparing it to a budget number. Returns a status message."
)
def check_price_deal_action(price_text: str, budget: float) -> ActionResult:
    """A simple wrapper that calls the real implementation."""
    return custom_actions.check_price_deal(price_text, budget)
