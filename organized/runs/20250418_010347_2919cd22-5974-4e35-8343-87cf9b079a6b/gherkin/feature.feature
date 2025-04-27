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

Scenario: Fill in the Username as 'standard_user', the Password as 'secret_sauce', and click the 'Login' button.
  When I enter "standard_user" into field with index 1
  When I enter "secret_sauce" into field with index 2

Scenario: Click the 'Login' button to submit the credentials and log in.
  When I click on the input with index 3

Scenario: Confirm completion of the ultimate task with the 'done' action.
  And I successfully complete the task

