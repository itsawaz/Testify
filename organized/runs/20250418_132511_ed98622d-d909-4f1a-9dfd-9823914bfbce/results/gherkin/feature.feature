Feature: register a new user at http://103.140.219.4:5173/auth/login
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: register a new user at http://103.140.219.4:5173/auth/login
    Given I navigate to "http://103.140.219.4:5173/auth/login"
    When I click on the a
    And I enter "John" into the input
    And I enter "Doe" into the input
    And I enter "johndoe@example.com" into the input
    And I enter "P@ssw0rd123" into the input
    And I enter "P@ssw0rd123" into the input
    When I click on the input
    When I click on the input
    When I click on the button
    Then I should see that the task is complete
