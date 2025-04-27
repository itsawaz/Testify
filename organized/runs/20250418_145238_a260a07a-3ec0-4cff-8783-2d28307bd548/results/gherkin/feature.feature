Feature: As a user, I want to communicate with other users (peers, coaches) using both individual and group chat features so that I can network, share insights, collaborate, and build my sports community in a seamless, real-time manner. use email id: madhukar.cool09@gmail.com and password:Test@123    website: http://103.140.219.4:5173/auth/login
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: As a user, I want to communicate with other users (peers, coaches) using both individual and group chat features so that I can network, share insights, collaborate, and build my sports community in a seamless, real-time manner. use email id: madhukar.cool09@gmail.com and password:Test@123    website: http://103.140.219.4:5173/auth/login
    Given I navigate to "http://103.140.219.4:5173/auth/login"
    And I enter "madhukar.cool09@gmail.com" into the input
    And I enter "Test@123" into the input
    When I click on the button
    When I click on the a
    When I click on the div
    When I click on the a
    When I click on the button
    When I click on the div
    And I enter "Hello team, excited to collaborate!" into the textarea
    When I click on the textarea
    When I click on the div
    Then I should see that the task is complete
