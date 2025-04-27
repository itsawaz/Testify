Feature: -> go to goole.com \\r\\n-> Search for capital of india
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: -> go to goole.com \\r\\n-> Search for capital of india
    Given I navigate to "https://www.google.com"
    And I enter "capital of India" into the textarea
    When I click on the input
    Then I should see that the task is complete
