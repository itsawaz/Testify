Feature: 1. Launch browser\\r\\n2. Navigate to url \\'http://automationexercise.com\\'\\r\\n3. Verify that home page is visible successfully\\r\\n4. Click on \\'Signup / Login\\' button\\r\\n5. Verify \\'New User Signup!\\' is visible\\r\\n6. Enter name and email address\\r\\n7. Click \\'Signup\\' button\\r\\n8. End test
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: 1. Launch browser\\r\\n2. Navigate to url \\'http://automationexercise.com\\'\\r\\n3. Verify that home page is visible successfully\\r\\n4. Click on \\'Signup / Login\\' button\\r\\n5. Verify \\'New User Signup!\\' is visible\\r\\n6. Enter name and email address\\r\\n7. Click \\'Signup\\' button\\r\\n8. End test
    Given I navigate to "http://automationexercise.com"
    When I click on the a
    And I enter "John Doe" into the input
    And I enter "johndoe@example.com" into the input
    When I click on the button
    And I enter "Jane Smith" into the input
    And I enter "janesmith@example.com" into the input
    When I click on the input
    And I enter "janedoe.unique1@example.com" into the input
    When I click on the input
    And I enter "SecurePassword123" into the input
    When I click on the input
    When I click on the input
