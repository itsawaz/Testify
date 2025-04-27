Feature: go to google.com
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to google.com
    Given I navigate to "http://www.google.com"
    Then I should see that the task is complete
