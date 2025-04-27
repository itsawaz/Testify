Feature: go to google
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to google
    Given I navigate to "https://www.google.com"
    Then I should see that the task is complete
