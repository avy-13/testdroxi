import time
import pytest_check as check
from main import *


def test_task_2():
    run_sync_validation()


def test_task_3(login_trello):
    page = login_trello

    page.wait_for_selector('[data-testid="list"]')
    columns = page.locator('[data-testid="list"]')
    column_count = columns.count()
    print(f"Found {column_count} columns")

    for i in range(column_count):
        column = columns.nth(i)
        title = column.locator('[data-testid="list-header"]').inner_text()
        print(f"\n--- Checking Column: {title} ---")

        scroll_container = column.locator("[data-testid='list-cards']")

        previous_height = 0
        for _ in range(20):
            scroll_container.evaluate("el => el.scrollBy(0, el.scrollHeight)")
            time.sleep(0.3)
            current_height = scroll_container.evaluate("el => el.scrollHeight")
            if current_height == previous_height:
                break
            previous_height = current_height

        urgent_cards = column.locator(
            '[data-testid="list-card"]',
            has=page.locator('[data-testid="compact-card-label"]', has_text="Urgent")
        )

        for j in range(urgent_cards.count()):
            urgent_cards.nth(j).scroll_into_view_if_needed()
            time.sleep(0.2)

        count = urgent_cards.count()
        print(f"Found {count} urgent cards in '{title}'")

        for j in range(count):
            card = urgent_cards.nth(j)
            card_title = card.locator('[data-testid="card-name"]').inner_text()
            card_labels = card.locator('[data-testid="compact-card-label"]').all_inner_texts()
            print(f"Urgent Card: Title: {card_title}, Labels: {card_labels} (in column: {title})")

            card.click()

            try:
                if page.locator('[data-testid="description-content-area"]').is_visible():
                    description_lines = page.locator('[data-testid="description-content-area"] p').all_inner_texts()
                    description = "\n".join(description_lines)
                    print(f"    Description: {description}")

                elif page.locator('[data-testid="description-button"]').is_visible():
                    print("    Description:  No description set")

                else:
                    print("    Description: ️ Not found")

            except Exception as e:
                print(f"    Error reading description: {e}")

            page.locator('[data-testid="CloseIcon"]').click()
            time.sleep(0.5)


def test_task_4(login_trello):
    page = login_trello
    todo_column = page.locator('[data-testid="list"]', has_text="To Do")

    scroll_container = todo_column.locator("[data-testid='list-cards']")

    previous_height = 0
    for _ in range(20):
        scroll_container.evaluate("el => el.scrollBy(0, el.scrollHeight)")
        time.sleep(0.3)
        current_height = scroll_container.evaluate("el => el.scrollHeight")
        if current_height == previous_height:
            break
        previous_height = current_height

    card = todo_column.locator(
        '[data-testid="list-card"]',
        has=page.locator('[data-testid="card-name"]', has_text="summarize the meeting"))

    check.is_true(card.count() > 0, 'There is no card with the title summarize the meeting in To Do column')

    card_title = card.locator('[data-testid="card-name"]').inner_text()
    card_labels = card.locator('[data-testid="compact-card-label"]').all_inner_texts()
    card.click()

    description = ""
    time.sleep(3)
    try:
        if page.locator('[data-testid="description-content-area"]').is_visible():
            description_lines = page.locator('[data-testid="description-content-area"] p').all_inner_texts()
            description = "\n".join(description_lines)
        elif page.locator('[data-testid="description-button"]').is_visible():
            description = 'There is no description'
    except Exception as e:
        print(f'   Error reading description: {e}')

    page.locator('[data-testid="CloseIcon"]').click()

    check.equal(card_title, 'summarize the meeting',
                f'The title is:{card_title}, but should be "summarize the meeting"')
    check.equal(description, 'For all of us\nPlease do so',
                f'The description is: {description}, but should be "For all of us Please do so"')
    check.equal("New" in card_labels, True, f"'New' label missing on card: {card_title}")
