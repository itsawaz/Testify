Feature: go to https://www.saucedemo.com
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to https://www.saucedemo.com
    Given I navigate to "https://www.saucedemo.com"
    Then I should see that the task is complete
