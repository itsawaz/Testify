Feature: Test Case 1: Register User 1. Launch browser 2. Navigate to url \\'http://automationexercise.com\\' 3. Verify that home page is visible successfully 4. Click on \\'Signup / Login\\' button 5. Verify \\'New User Signup!\\' is visible 6. Enter name and email address 7. Click \\'Signup\\' button 8. Verify that \\'ENTER ACCOUNT INFORMATION\\' is visible 9. Fill details: Title, Name, Email, Password, Date of birth 10. Select checkbox \\'Sign up for our newsletter!\\' 11. Select checkbox \\'Receive special offers from our partners!\\' 12. Fill details: First name, Last name, Company, Address, Address2, Country, State, City, Zipcode, Mobile Number 13. Click \\'Create Account button\\' 14. Verify that \\'ACCOUNT CREATED!\\' is visible 15. Click \\'Continue\\' button 16. Verify that \\'Logged in as username\\' is visible 17. Click \\'Delete Account\\' button 18. Verify that \\'ACCOUNT DELETED!\\' is visible and click \\'Continue\\' button
  As a user
  I want to automate browser interactions
  So that I can achieve my task without manual intervention

  Scenario: Test Case 1: Register User 1. Launch browser 2. Navigate to url \\'http://automationexercise.com\\' 3. Verify that home page is visible successfully 4. Click on \\'Signup / Login\\' button 5. Verify \\'New User Signup!\\' is visible 6. Enter name and email address 7. Click \\'Signup\\' button 8. Verify that \\'ENTER ACCOUNT INFORMATION\\' is visible 9. Fill details: Title, Name, Email, Password, Date of birth 10. Select checkbox \\'Sign up for our newsletter!\\' 11. Select checkbox \\'Receive special offers from our partners!\\' 12. Fill details: First name, Last name, Company, Address, Address2, Country, State, City, Zipcode, Mobile Number 13. Click \\'Create Account button\\' 14. Verify that \\'ACCOUNT CREATED!\\' is visible 15. Click \\'Continue\\' button 16. Verify that \\'Logged in as username\\' is visible 17. Click \\'Delete Account\\' button 18. Verify that \\'ACCOUNT DELETED!\\' is visible and click \\'Continue\\' button
    Given I navigate to "http://automationexercise.com"
    When I click on the a
    And I enter "Test User" into the input
    And I enter "testuser@example.com" into the input
    When I click on the input
    And I enter "uniqueemail@example.com" into the input
    When I click on the input
    Given I navigate to "https://automationexercise.com/signup"
    And I enter "New User" into the input
    And I enter "newuniqueemail@example.com" into the input
    When I click on the input
    When I click on the input
    And I enter "SecurePassword123" into the input
    When I click on the input
    When I click on the input
    And I enter "John" into the input
    And I enter "Doe" into the input
    And I enter "Automation Corp" into the input
    And I enter "123 Street Name" into the input
    And I enter "Suite 456" into the input
    And I enter "California" into the input
    And I enter "Los Angeles" into the input
    And I enter "90001" into the input
    And I enter "1234567890" into the input
    And I enter "+1234567890" into the a
    And I enter "+1234567890" into the input
    When I click on the input
    When I click on the a
    When I click on the a
    When I click on the a
    Then I should see that the task is complete
