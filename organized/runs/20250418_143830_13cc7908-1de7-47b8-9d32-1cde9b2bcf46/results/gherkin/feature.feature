Feature: go to i am game at http://103.140.219.4:5173/auth/login -> login id: madhukar.cool09@gmail.com password: Test@123 ->  make a dummy post -> logout
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to i am game at http://103.140.219.4:5173/auth/login -> login id: madhukar.cool09@gmail.com password: Test@123 ->  make a dummy post -> logout
    Given I navigate to "http://103.140.219.4:5173/auth/login"
    And I enter "madhukar.cool09@gmail.com" into the input
    And I enter "Test@123" into the input
    When I click on the input
    When I click on the button
    And I enter "This is a dummy post created for testing purposes." into the textarea
    When I click on the textarea
    When I click on the button
    When I click on the button
    When I click on the element with index 1
    When I click on the element with index 0
    When I click on the element with index 9
    When I click on the a
