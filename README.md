# Borrow
My CS50 Final project and it's writeup which I am directly uploading to GitHub
## YouTube URL
https://youtu.be/993B34z99Uc?si=lcHSnWwzSAjO1jzQ
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
# Part by part explanations:
### The cryptography, pywebpush parts
used to send push notifications to users when they receive a request for money
### The SQL part
The SQL part consists of 4 tables, namely:
- requests
- transactions
- users
- push_subscriptions
The requests table has the rows of requests: request ID, borrower_ID, lender_ID, and amount.
The users table has the username and the user's password, which is hashed using the `werkzug.security` `check_password_hash` utility and `generate_password_hash` utility. The transactions table has the transaction ID, the borrower ID, the lender ID, and the amount. The push_subscription has the user's ID and subscription JSON, which is used for the notification utility.
The transaction table has the list of all the transactions that are done with the transaction ID, lender ID, borrower ID and amount.
The push subscription table was made with the help of AI. It is used for storing the VAPID keys so that notification subscription works.
## The log in & register flow
The website has a built-in login/register flow, which uses an SQL table to store the user name and the hashed version of their password in the table called `users`. It also checks for:
- missing user names
- missing passwords
- missing confirmed passwords
It checks if the password and confirmed password match.
## The index page
On the index page, we need to display:
- the borrower's name
- the lend person's name
- the amount
- a button to repay to the person if we have borrowed from them
To get the name of the person, only the transaction ID or the user's ID is stored in the transactions table. We perform an SQL JOIN function which can gather it, join the tables, and get the names of the people.
## The request page
The request page shows a dropdown menu of all the people who are registered on the page from whom we can request money. The text input lets you input the amount of money you want to request from that person. Clicking on request makes an SQL database command which puts the borrower's ID (which is our ID), the lender's ID (which is the other person's ID), and the amount into the request table. It automatically gets populated in the lend page for the person whom we have clicked as the lender.
It also has an AI-generated notification algorithm which would send a notification to the user if they have notifications on from their browser about who has asked for the borrow request and the amount of money which was in the borrow request. It comes up as a notification from their browser.
## The lend page
The lend page shows all the pending requests sent using the borrow page to you. It shows up in a table with a tick button, which can be used to agree to pay the amount, and a cross button, which can be used to reject it.
Pressing the tick goes to the transaction page and, upon completion of the transaction, adds to the transaction table and adds it to that user's dashboard in index.html. By doing reject, it just removes it from the requests table.
## The repay page
Shows the borrowed table from index.html with the repay buttons for quick access
## The handle_request route
This is not a web page. It is just a route which is used to gather information on whether they press the tick or wrong, or to gather the repay button's click and the person who must be transacted. It automatically calls the transact page based on the set requirements with the correct arguments used for the transact page so that the transaction goes smoothly.
## The payment page
The payment page is a dummy payment interface which was made just for simulating a card payment. It has all the constraints of a credit card, like the credit card number being a particular number of characters long and the expiry date and CVV number. It also has a graphic on an SVG which will update the credit card number onto the SVG as we type it. It is made using JavaScript. All it does is simulate doing a transaction from one side to the other. It does not link to any real payment gateway. It is just for simulation purposes only.
## The VAPID_PUBLIC_KEY route
The VAPID public key route is used for storing the public key of the user and returning it using JSONify.
