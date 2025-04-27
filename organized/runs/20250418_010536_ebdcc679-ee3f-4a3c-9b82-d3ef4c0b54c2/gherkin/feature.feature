Feature: go to https://www.saucedemo.com/ -> login
  As an automated agent
  I want to perform the task: go to https://www.saucedemo.com/ -> login
  So that I can demonstrate browser automation

Background:
  Given the task involves navigating multiple pages
  And page 1 is Unknown Page at about:blank
  And page 2 is Swag Labs at https://www.saucedemo.com/
  And page 3 is Swag Labs at https://www.saucedemo.com/inventory.html

Scenario: Initial task
  Given I navigate to "https://www.saucedemo.com/"

Scenario: Enter Username 'standard_user' and Password 'secret_sauce' into the respective fields and click the Login button to log in.
  When I enter "standard_user" into field with index 1
  When I enter "secret_sauce" into field with index 2

Scenario: Click the Login button to proceed with logging in.
  When I click on the input with index 3

Scenario: Finalize the task since the ultimate goal of logging into the website has been achieved.
  And I successfully complete the task

