Feature: go to http://sahanalogistics.com/tms/Login.aspx -> id : admin and password : admin ->  go to tms -> logout
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to http://sahanalogistics.com/tms/Login.aspx -> id : admin and password : admin ->  go to tms -> logout
    Given I navigate to "http://sahanalogistics.com/tms/Login.aspx"
    And I enter "admin" into the input
    And I enter "admin" into the input
    When I click on the input
    When I click on the button
    When I click on the a
    Then I should see that the task is complete
