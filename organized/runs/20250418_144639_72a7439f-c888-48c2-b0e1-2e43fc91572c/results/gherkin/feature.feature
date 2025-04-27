Feature: go to i am game at http://103.140.219.4:5173/auth/login -> login id: madhukar.cool09@gmail.com password: Test@123 ->  make a dummy post -> then go to user profile -> edit the username name to madukar  ->find the  logout option -> logout
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to i am game at http://103.140.219.4:5173/auth/login -> login id: madhukar.cool09@gmail.com password: Test@123 ->  make a dummy post -> then go to user profile -> edit the username name to madukar  ->find the  logout option -> logout
    Given I navigate to "http://103.140.219.4:5173/auth/login"
    And I enter "madhukar.cool09@gmail.com" into the input
    And I enter "Test@123" into the input
    When I click on the input
    When I click on the button
    And I enter "This is a dummy post." into the textarea
    When I click on the textarea
    When I click on the button
    When I click on the a
    When I click on the div
    And I enter "madukar" into the input
    When I click on the input
    When I click on the li
    Then I should see that the task is complete
