Feature: Make persistent

    Scenario: run a simple make persistent
        Given 'Person' from 'model.company' is imported
        And 'Company' from 'model.company' is imported
        And session is initialized
        When create a 'Person' object with params
        And create 'mama' object of class 'Person'
        And call make_persistent to 'mama' 
        Then Is persistent


   