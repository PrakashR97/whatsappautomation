from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError
)

import time
import os
import json
import csv

from datetime import datetime


contacts = [
    {
        "name": "Prakash",
        "number": "9876543210",
        "message": "Hi {name}, this is a personalized message."
    },
    {
        "name": "Indhu",
        "number": "9876543211",
        "message": "Hello {name}, hope you are doing well!"
    },
    {
        "name": "Nataraj",
        "number": "9876543211",
        "message": "Hello {name}, hope you are doing well!"
    },
    {
        "name": "Balaji",
        "number": "9876543211",
        "message": "Hello {name}, hope you are doing well!"
    }
]


# ============================================================
# FOLDERS
# ============================================================

os.makedirs("screenshots", exist_ok=True)
os.makedirs("error_screenshots", exist_ok=True)


# ============================================================
# OUTPUT FILES
# ============================================================

json_file = "whatsapp_results.json"
csv_file = "whatsapp_results.csv"

results = []


# ============================================================
# SAVE JSON
# ============================================================

def save_results():

    with open(
        json_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"JSON updated: {json_file}")


# ============================================================
# SAVE CSV / APPLE NUMBERS
# ============================================================

def save_to_csv():

    headers = [
        "Name",
        "Number",
        "Last Message 1",
        "Last Message 2",
        "Last Message 3",
        "Personalized Message",
        "Status",
        "Screenshot",
        "Error",
        "Processed At"
    ]

    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        # ----------------------------------------------------
        # Headers
        # ----------------------------------------------------

        writer.writerow(headers)

        # ----------------------------------------------------
        # Data
        # ----------------------------------------------------

        for result in results:

            last_messages = result.get(
                "last_3_messages",
                []
            )

            writer.writerow([
                result.get("name", ""),
                result.get("number", ""),

                last_messages[0]
                if len(last_messages) > 0
                else "",

                last_messages[1]
                if len(last_messages) > 1
                else "",

                last_messages[2]
                if len(last_messages) > 2
                else "",

                result.get(
                    "personalized_message",
                    ""
                ),

                result.get(
                    "status",
                    ""
                ),

                result.get(
                    "screenshot",
                    ""
                ),

                result.get(
                    "error",
                    ""
                ),

                result.get(
                    "processed_at",
                    ""
                )
            ])

    print(
        f"CSV updated: {csv_file}"
    )


# ============================================================
# PLAYWRIGHT
# ============================================================

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    try:

        # ====================================================
        # OPEN WHATSAPP
        # ====================================================

        page.goto(
            "https://web.whatsapp.com",
            wait_until="domcontentloaded"
        )

        print("Opening WhatsApp Web...")
        print("Scan QR code if required.")

        page.wait_for_timeout(30000)

        # ====================================================
        # PROCESS CONTACTS
        # ====================================================

        for contact in contacts:

            name = contact["name"]
            number = contact["number"]

            print("\n" + "=" * 60)

            print(
                f"Processing: {name} - {number}"
            )

            print("=" * 60)

            # ------------------------------------------------
            # Default result
            # ------------------------------------------------

            result_data = {

                "name": name,

                "number": number,

                "last_3_messages": [],

                "personalized_message": None,

                "status": "FAILED",

                "screenshot": None,

                "error": None,

                "processed_at": None
            }

            try:

                # ============================================
                # 1. PERSONALIZED MESSAGE
                # ============================================

                message = contact[
                    "message"
                ].replace(
                    "{name}",
                    name
                )

                result_data[
                    "personalized_message"
                ] = message

                # ============================================
                # 2. SEARCH
                # ============================================

                print(
                    "Finding search box..."
                )

                search_box = page.get_by_role(
                    "textbox",
                    name="Search"
                )

                search_box.wait_for(
                    state="visible",
                    timeout=30000
                )

                search_box.click()

                search_box.fill("")

                search_box.fill(name)

                print(
                    f"Searching: {name}"
                )

                page.wait_for_timeout(3000)

                # ============================================
                # 3. OPEN CHAT
                # ============================================

                result = page.get_by_text(
                    name,
                    exact=True
                ).first

                try:

                    result.wait_for(
                        state="visible",
                        timeout=10000
                    )

                    result.click()

                except PlaywrightTimeoutError:

                    print(
                        f"Name '{name}' not found."
                    )

                    print(
                        "Trying phone number..."
                    )

                    result = page.get_by_text(
                        number,
                        exact=False
                    ).first

                    result.wait_for(
                        state="visible",
                        timeout=10000
                    )

                    result.click()

                print(
                    f"Chat opened: {name}"
                )

                page.wait_for_timeout(3000)

                # ============================================
                # 4. LAST 3 MESSAGES
                # ============================================

                print(
                    "Extracting last 3 messages..."
                )

                messages = page.locator(
                    '[data-testid="msg-container"]'
                )

                message_count = messages.count()

                print(
                    f"Messages found: "
                    f"{message_count}"
                )

                start_index = max(
                    0,
                    message_count - 3
                )

                for i in range(
                    start_index,
                    message_count
                ):

                    try:

                        text = messages.nth(
                            i
                        ).inner_text().strip()

                        if text:

                            result_data[
                                "last_3_messages"
                            ].append(text)

                    except Exception as e:

                        print(
                            f"Could not extract "
                            f"message {i}: {e}"
                        )

                print(
                    "Last 3 messages:"
                )

                for msg in result_data[
                    "last_3_messages"
                ]:

                    print(
                        f"- {msg}"
                    )

                # ============================================
                # 5. MESSAGE BOX
                # ============================================

                message_box = page.get_by_role(
                    "textbox",
                    name="Type a message"
                )

                message_box.wait_for(
                    state="visible",
                    timeout=30000
                )

                # ============================================
                # 6. TYPE MESSAGE
                # ============================================

                message_box.click()

                message_box.fill(
                    message
                )

                print(
                    f"Message: {message}"
                )

                # ============================================
                # 7. SEND
                # ============================================

                send_button = page.get_by_role(
                    "button",
                    name="Send"
                )

                try:

                    send_button.wait_for(
                        state="visible",
                        timeout=5000
                    )

                    send_button.click()

                except PlaywrightTimeoutError:

                    print(
                        "Send button not found."
                    )

                    print(
                        "Trying Enter..."
                    )

                    message_box.press(
                        "Enter"
                    )

                print(
                    "Message sent."
                )

                # ============================================
                # 8. WAIT
                # ============================================

                page.wait_for_timeout(
                    3000
                )

                # ============================================
                # 9. SCREENSHOT
                # ============================================

                safe_name = "".join(
                    c
                    for c in name
                    if c.isalnum()
                    or c in (
                        " ",
                        "_",
                        "-"
                    )
                )

                screenshot_path = (
                    f"screenshots/"
                    f"{safe_name}.png"
                )

                page.screenshot(
                    path=screenshot_path,
                    full_page=False
                )

                # ============================================
                # 10. SUCCESS
                # ============================================

                result_data[
                    "status"
                ] = "SUCCESS"

                result_data[
                    "screenshot"
                ] = screenshot_path

                result_data[
                    "processed_at"
                ] = datetime.now().isoformat()

                print(
                    f"Screenshot saved: "
                    f"{screenshot_path}"
                )

                print(
                    f"SUCCESS: {name}"
                )

            # =================================================
            # TIMEOUT ERROR
            # =================================================

            except PlaywrightTimeoutError as e:

                result_data[
                    "error"
                ] = (
                    "TimeoutError: "
                    + str(e)
                )

                result_data[
                    "processed_at"
                ] = datetime.now().isoformat()

                print(
                    f"TIMEOUT for {name}"
                )

                print(e)

                try:

                    safe_name = "".join(
                        c
                        for c in name
                        if c.isalnum()
                        or c in (
                            " ",
                            "_",
                            "-"
                        )
                    )

                    error_path = (
                        f"error_screenshots/"
                        f"{safe_name}_timeout.png"
                    )

                    page.screenshot(
                        path=error_path,
                        full_page=False
                    )

                except Exception:
                    pass

            # =================================================
            # PLAYWRIGHT ERROR
            # =================================================

            except PlaywrightError as e:

                result_data[
                    "error"
                ] = (
                    "PlaywrightError: "
                    + str(e)
                )

                result_data[
                    "processed_at"
                ] = datetime.now().isoformat()

                print(
                    f"PLAYWRIGHT ERROR "
                    f"for {name}"
                )

                print(e)

            # =================================================
            # OTHER ERROR
            # =================================================

            except Exception as e:

                result_data[
                    "error"
                ] = (
                    f"{type(e).__name__}: "
                    f"{str(e)}"
                )

                result_data[
                    "processed_at"
                ] = datetime.now().isoformat()

                print(
                    f"ERROR for {name}"
                )

                print(
                    f"{type(e).__name__}: {e}"
                )

            # =================================================
            # SAVE JSON + CSV AFTER EVERY CONTACT
            # =================================================

            results.append(
                result_data
            )

            save_results()

            save_to_csv()

            print(
                "JSON and CSV updated."
            )

            # Wait before next contact

            page.wait_for_timeout(
                2000
            )

        # ====================================================
        # COMPLETE
        # ====================================================

        print("\n" + "=" * 60)

        print(
            "ALL CONTACTS PROCESSED"
        )

        print("=" * 60)

        print(
            f"JSON: {json_file}"
        )

        print(
            f"CSV: {csv_file}"
        )

        time.sleep(10)

    finally:

        browser.close()