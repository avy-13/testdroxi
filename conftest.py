import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def playwright_instance():
    pw = sync_playwright().start()
    yield pw
    pw.stop()


@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="function")
def login_trello(page):
    page.goto("https://trello.com/b/2GzdgPlw/droxi")
    page.click("text=Log in")
    page.fill("input[id='username-uid1']", "droxiautomation@gmail.com")
    page.click("button[id='login-submit']")
    page.fill("input[id='password']", "Droxination013!")
    page.click("button[id='login-submit']")
    yield page