# Stock Education

Stock Education is a virtual stock market designed to help educate students on how the stock market works. Students can learn how basic buying and selling of stock shares work and how to understand the various statistics about a company’s stock.  Students can be easily organized into classrooms, where the teacher can view each student’s portfolio and history.  Each student has the ability to buy and sell stocks, view stock quotes and news, see their own purchase history, and join groups.  As a teacher or individual, the ability to create and manage groups

*****

This project satisfies all distinctiveness and complexity requirements for CS50’s Web Programming final capstone. This project is not an encyclopedia, e-commerce service, email service, social network, or food ordering service. This program is an educational tool for the stock market and is distinctly different from other CS50-Web projects. Stock Education utilizes Django on the back-end and meets the necessary Django model requirements with four models.  Javascript is used for creating a live search box, manipulating stock graphs, creating pop-overs and carousels, and making API calls for data.  Finally, Stock Education is mobile-responsive.

*****

The Final_Project directory contains the Django project for Stock Education. The stocks directory contains the stocks app. The static directory contains the CSS and Javascript for Stock Education. `Live.js` handles the API calls and data necessary for the live search boxes.  `Quoted.js` handles all of the functionality for the quoted page. It creates the stock graph, changes the graph color for increase or decrease, creates the pop-over explanations for stock statistics, and creates the news article carousel. The templates directory contains all of the HTML pages for Stock Education. `Functions.py` contains some helper functions for looking up a quote, formatting to dollars, and shortening large numbers. `Models.py` has the models for a user, stock, transaction, and group. `Urls.py` contains all of the apps URL patterns, and `views.py` contains the majority of the application.  Lastly, the requirement.txt file contains a list of the necessary python packages.

*****

In order to run Stock Education you must first get an [IEX Cloud api key](https://iexcloud.io/), an [Alpha Vantage api key](https://www.alphavantage.co/), and a [Financial Modeling Prep api key](https://financialmodelingprep.com/developer). The set these as environment variables `IEX_KEY`, `ALPHA_KEY`, and `FMP_KEY` respectively. Next install all the required packages, make and apply migrations, and run the server. Once the server is set up, you can use Stock Education the way a regular user would. If you want to use all the features of Stock Education, select “teacher” when creating an account. Once this is done, you are set up and ready to test out the virtual stock market.

*****

This project is a continuation and upgrade of my CS50 final project. Since the original was written in Flask, I re-wrote the entire program in Django. I improved the live search box and group features. I also added the color changing feature of the graph, more statistics, pop-overs, and the news article carousel. I also added the ability to see the exchange and percent increase/decrease along with general improvements and bug fixes.  
The multiple API keys are necessary in order to keep Stock Education free. 


 