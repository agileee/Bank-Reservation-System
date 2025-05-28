# Group Project

The Bank Management System is a web-based application developed using Flask (Python) for the backend, HTML/CSS for the frontend, and MySQL for database management. The primary aim of the system is to simulate core banking functions such as user registration, profile
management, loan applications, and transaction tracking in a secure and efficient way.

## Features

- User Authentication
    ● Login/Registration System using secure password handling.
    ● Each user has a unique profile with access to personal banking details.
  
- Dashboard
    ● Displays user information, balance, recent transactions, and loan status.
  
- Profile Management
    ● Users can view and update their profile details.
    ● Clean and responsive UI for ease of navigation.
  
- Loan Application
    ● Users can submit loan requests.
    ● The system validates the data and stores the loan application in the database.
  
- Transactions
    ● Users can initiate money transfers by entering:
          ○ Sender and receiver details
          ○ Transaction PIN
          ○ Date and time
    ● Each transaction is recorded and can be viewed in the transaction history

- Transaction History
    ● A dedicated page to view past transactions with filtering by client.
    ● Each client has a separate transactions table for better data management and security.
  
- Logout
    ● After the required details are taken logging out will be taken back to the main page.

## How to Run

Set-ExecutionPolicy Unrestricted -Scope Process
.\env\Scripts\Activate

Type these code in command line and activate virtual environment.

use code:
python app.py 
to set up localhost connection.

## Authors

Akhil 
(github.com/agileee)
&
Ashwini Crasta

