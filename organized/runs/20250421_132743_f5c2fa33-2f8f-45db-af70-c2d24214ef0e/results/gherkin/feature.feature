Feature: go to http://103.140.219.4:5173/auth/login -> use id:madhukar.cool09@gmail.com password: Test@123 -> make a demo blog post
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to http://103.140.219.4:5173/auth/login -> use id:madhukar.cool09@gmail.com password: Test@123 -> make a demo blog post
    Given I navigate to "http://103.140.219.4:5173/auth/login"
    And I enter "madhukar.cool09@gmail.com" into the input
    And I enter "Test@123" into the input
    When I click on the button
    And I enter "This is a demo blog post created by automation." into the textarea
    When I click on the textarea
    When I click on the button
    Then I should see that the task is complete
