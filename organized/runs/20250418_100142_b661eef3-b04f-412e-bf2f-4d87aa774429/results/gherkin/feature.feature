Feature: go to goole.com
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to goole.com
    Given I navigate to "https://google.com"
    Then I should see that the task is complete
