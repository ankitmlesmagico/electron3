

from browser_use import ActionResult, Controller
from browser_use.browser import BrowserSession 
import logging
import os
import asyncio
from pathlib import Path
import httpx
from pydantic import BaseModel 
from typing import List 

logger = logging.getLogger("CUSTOM_ACTIONS")

DOWNLOADS_DIR = Path(os.getcwd()) / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

def pause_and_wait_for_user(reason: str):
    """
    This is the core logic for pausing the agent. It prints the reason
    and waits for the user to press Enter in the terminal.
    """
    print("-" * 60)
    print(f"⏸️  AGENT PAUSED: {reason}")
    print(">>> Please complete the required action in the browser window. <<<")
    print(">>> When you are finished, press [Enter] here to continue.   <<<")
    print("-" * 60)
    
    
    input() 
    
    logger.info("User pressed [Enter]. Resuming agent.")
    return ActionResult(
        long_term_memory="The user has completed a manual action.",
        extracted_content="User has completed the manual step. Resuming."
    )



async def click_and_upload(selector_index: int, file_path: str, browser_session: BrowserSession):
    """
    Handles file uploads atomically. It finds an element by its browser-use index,
    clicks it to open the file dialog, and then uploads the specified file.
    This prevents race conditions.
    """
    if not os.path.isabs(file_path):
        return ActionResult(error=f"File path must be an absolute path. You provided: '{file_path}'")
    if not os.path.exists(file_path):
        return ActionResult(error=f"File not found at path: {file_path}. Cannot upload.")

    logger.info(f"Preparing to click element at index {selector_index} and then upload {file_path}...")
    
    try:
        active_page = browser_session.browser.contexts[0].pages[-1]
        
        async with active_page.expect_file_chooser(timeout=10000) as fc_info:
            # Find the element provided by browser-use's state
            element_to_click_dom = await browser_session.get_dom_element_by_index(selector_index)
            if not element_to_click_dom:
                return ActionResult(error=f"Could not find element with index {selector_index} to click.")
            
            # Get the Playwright locator for that element and click it
            element_to_click_locatable = await browser_session.get_locate_element(element_to_click_dom)
            await element_to_click_locatable.click()

        
        file_chooser = await fc_info.value
        await file_chooser.set_files(file_path)

        success_msg = f"Successfully clicked element {selector_index} and set file for upload: {file_path}"
        logger.info(success_msg)
        return ActionResult(extracted_content=success_msg, long_term_memory="The file has been selected for upload.")

    except asyncio.TimeoutError:
        error_msg = ("Upload failed: The file chooser dialog did not open after clicking the element. "
                     "Please ensure the element index corresponds to a button that opens a file dialog.")
        logger.error(error_msg)
        return ActionResult(error=error_msg)
    except Exception as e:
        error_msg = f"An error occurred during the click-and-upload operation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return ActionResult(error=error_msg)


async def download_file(browser_session: BrowserSession):
    """Waits for a standard download event (e.g., after a button click)."""
    
    logger.info("Waiting for a standard download to start...")
    try:
        active_page = browser_session.browser.contexts[0].pages[-1]
        async with active_page.expect_download(timeout=15000) as download_info:
            download = await download_info.value
        save_path = await download.path()
        absolute_path = str(Path(save_path).resolve())
        success_msg = f"Successfully downloaded '{download.suggested_filename}' to: {absolute_path}"
        logger.info(success_msg)
        return ActionResult(
            extracted_content=success_msg,
            long_term_memory=f"The file was saved to the absolute path: {absolute_path}"
        )
    except asyncio.TimeoutError:
        return ActionResult(error="Download failed. No download was initiated within 15 seconds.")
    except Exception as e:
        return ActionResult(error=f"An unexpected error occurred during download: {str(e)}")

async def save_displayed_file(filename: str, browser_session: BrowserSession, downloads_dir: Path):
    """
    Saves content from the current URL to a SPECIFIED downloads directory.
    This tool is now more robust as it doesn't have to guess the path.
    """
    logger.info(f"Attempting to save displayed file as '{filename}' to '{downloads_dir}'...")
    try:
        active_page = browser_session.browser.contexts[0].pages[-1]
        current_url = active_page.url

        
        base64_content = await active_page.evaluate(f"""
            async (url) => {{
                const response = await fetch(url);
                const blob = await response.blob();
                const reader = new FileReader();
                return new Promise(resolve => {{
                    reader.onload = () => resolve(reader.result.split(',')[1]);
                    reader.readAsDataURL(blob);
                }});
            }}
        """, current_url)

        if not base64_content:
            return ActionResult(error="Failed to fetch file content from the browser.")

        import base64
        file_bytes = base64.b64decode(base64_content)

        
        save_path = downloads_dir / filename
        
        with open(save_path, 'wb') as f:
            f.write(file_bytes)

        absolute_path = str(save_path.resolve())
        success_msg = f"Successfully saved displayed file '{filename}' to: {absolute_path}"
        logger.info(success_msg)
        
        return ActionResult(
            extracted_content=success_msg,
            long_term_memory=f"The file was saved to the absolute path: {absolute_path}"
        )
    except Exception as e:
        error_msg = f"An error occurred while saving the displayed file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return ActionResult(error=error_msg)
    

    
def check_price_deal(price_text: str, budget: float) -> ActionResult:
    """
    Accepts a price string (e.g., "$1,299.99") and a budget number.
    It cleans the price string, converts it to a float, and checks if it's
    below or equal to the budget. Returns a clear status message.
    This is a non-browser, local processing tool.
    """
    logger.info(f"Checking if price '{price_text}' is within budget of ${budget}...")
    
    try:
        # Clean the price string using standard Python methods
        cleaned_price_str = price_text.replace('$', '').replace(',', '').strip()
        price_value = float(cleaned_price_str)

        # The core business logic
        if price_value <= budget:
            deal_status = f"GOOD DEAL: The price ${price_value:,.2f} is within the ${budget:,.2f} budget."
            logger.info(deal_status)
        else:
            deal_status = f"NO DEAL: The price ${price_value:,.2f} is above the ${budget:,.2f} budget."
            logger.info(deal_status)
        
        # Return the status message for the agent to use
        return ActionResult(
            extracted_content=deal_status,
            long_term_memory=deal_status # Also save to memory
        )

    except (ValueError, TypeError) as e:
        error_msg = f"Could not parse the price string '{price_text}'. Error: {e}"
        logger.error(error_msg)
        return ActionResult(error=error_msg)