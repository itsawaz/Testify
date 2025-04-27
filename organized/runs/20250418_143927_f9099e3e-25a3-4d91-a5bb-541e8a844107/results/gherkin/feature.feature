Feature: go to this page http://sahanalogistics.com/tms/default.aspx username: admin , password: admin
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: go to this page http://sahanalogistics.com/tms/default.aspx username: admin , password: admin
    Given I navigate to "http://sahanalogistics.com/tms/default.aspx"
    And I enter "admin" into the input
    And I enter "admin" into the input
    When I click on the input
    Then I should see that the task is complete
