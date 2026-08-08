# Borrow
My CS50 Final project and it's writeup which I am directly uploading to GitHub
## Use
It's a simple project used to keep track of, lend, request and repay borrowed money through a web portal.
## How does it work?
It uses flask, HTML, JS and CSS and runs on the flask server
## Explanation / overview of project
 This is a simple project in which there is a login page, and after logging in, we get a dashboard in which we can see from whom we have borrowed money and from whom we have lent money to.
- The Borrowed Money page has the option to return the money back to the other person.
- The next page we can see is the Request page, where we can request money from all the users on the website and how much money we need. You can click on the request button.
- The next page is the Lend page, where we can accept the requests of people who have asked for money from us. These requests, when accepted, will prompt a payment window, which is a simple gateway that I made, from which they can "pay their money. After success, it will transact that money."
- The last page is the Repay page, where you can see exactly who all you have borrowed money from and easily repay from there.
# File by file explanations:
# app.py
### The cryptography, pywebpush parts
used to send push notifications to users when they receive a request for money
### The SQL part 
The SQL part consists of 4 tables, namely:
- requests
- transactions
- users
- push_subscriptions
The requests table has the rows of requests: request ID, borrower_ID, lender_ID, and amount. The users table has the username and the user's password, which is hashed using the `wakezug.security` `check_password_hash` utility and `generate_password_hash` utility. The transactions table has the transaction ID, the borrower ID, the lender ID, and the amount. The push_subscription has the user's ID and subscription JSON, which is used for the notification utility.
