Feature: Test Case : Register User\\r\\n1. Launch browser\\r\\n2. Navigate to url \\'http://automationexercise.com\\'\\r\\n3. Verify that home page is visible successfully\\r\\n4. Click on \\'Signup / Login\\' button\\r\\n5. Verify \\'New User Signup!\\' is visible\\r\\n6. Enter name and email address\\r\\n7. Click \\'Signup\\' button\\r\\n8. End test
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: Test Case : Register User\\r\\n1. Launch browser\\r\\n2. Navigate to url \\'http://automationexercise.com\\'\\r\\n3. Verify that home page is visible successfully\\r\\n4. Click on \\'Signup / Login\\' button\\r\\n5. Verify \\'New User Signup!\\' is visible\\r\\n6. Enter name and email address\\r\\n7. Click \\'Signup\\' button\\r\\n8. End test
    Given I navigate to "http://automationexercise.com"
    When I click on the a
    And I enter "Test User" into the input
    And I enter "testuser@example.com" into the input
    When I click on the button
    And I enter "testusernew@example.com" into the input
    When I click on the input
    When I click on the input
    And I enter "password123" into the input
    And I enter "John" into the input
    And I enter "Doe" into the input
    And I enter "TechCorp" into the input
    And I enter "123 Tech Street" into the input
    And I enter "Apartment 4B" into the input
    And I enter "California" into the input
    And I enter "San Francisco" into the input
    And I enter "Apartment 4B" into the input
    And I enter "California" into the input
    And I enter "San Francisco" into the input
    And I enter "94107" into the input
    And I enter "1234567890" into the input
