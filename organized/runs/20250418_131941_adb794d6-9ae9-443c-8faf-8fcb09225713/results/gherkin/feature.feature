Feature: go to https://www.saucedemo.com/ -> login -> add a product to cart -> checkout -> logut
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to https://www.saucedemo.com/ -> login -> add a product to cart -> checkout -> logut
    Given I navigate to "https://www.saucedemo.com/"
    And I enter "standard_user" into the input
    And I enter "secret_sauce" into the input
    When I click on the input
    When I click on the button
    When I click on the a
    When I click on the button
    And I enter "John" into the input
    And I enter "Doe" into the input
    And I enter "12345" into the input
    When I click on the input
    When I click on the button
    When I click on the div
    When I click on the div
    When I click on the div
    When I click on the button
    When I click on the a
    Then I should see that the task is complete
