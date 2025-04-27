Feature: go to https://www.saucedemo.com/ -> login
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to https://www.saucedemo.com/ -> login
    Given I navigate to "https://www.saucedemo.com"
    And I enter "standard_user" into the input
    And I enter "secret_sauce" into the input
    When I click on the input
    Then I should see that the task is complete
