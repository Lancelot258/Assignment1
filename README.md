# Dining Concierge Chatbot

## Overview
This project is a **serverless, microservice-driven web application** that implements a **Dining Concierge Chatbot**. The chatbot provides restaurant recommendations based on user preferences using **AWS services** such as **Lex, Lambda, API Gateway, DynamoDB, SQS, SES, and OpenSearch (Elasticsearch)**.

---

## Features
- **Frontend Deployment** - A web interface to interact with the chatbot (hosted on AWS S3).
- **API Development** - API Gateway with Lambda functions to handle chatbot communication.
- **Lex Chatbot** - Handles user interactions with intents like `GreetingIntent`, `ThankYouIntent`, and `DiningSuggestionsIntent`.
- **DynamoDB Integration** - Stores restaurant data retrieved from Yelp API.
- **OpenSearch (Elasticsearch)** - Indexes restaurant data for quick search.
- **SQS & SES Integration** - Asynchronously processes user requests and sends restaurant suggestions via email.

---

## **Project Architecture**
1. User interacts with the **frontend chatbot** (deployed on AWS S3).
2. The frontend sends requests to the **API Gateway**.
3. API Gateway triggers **Lambda function**, which:
   - Passes the request to **Amazon Lex**.
   - Lex processes user queries using **predefined intents** and a **Lambda function**.
4. The chatbot collects user preferences (**location, cuisine, time, number of people, email**) and stores them in an **SQS queue**.
5. A **background Lambda function** retrieves requests from SQS:
   - Fetches restaurant recommendations from **OpenSearch & DynamoDB**.
   - Formats the recommendations and sends them to the user via **SES (Simple Email Service)**.

---

## **Setup Instructions**

### **1. Clone the Repository**
```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
```

### **2. Deploy the Frontend**
The frontend is based on the cloud-hw1-starter template.
Deploy it on AWS S3 for hosting.
Follow the AWS S3 website hosting guide.

### **3. Setup API Gateway & Lambda Functions**
Import the Swagger API definition:
```bash
https://github.com/001000001/aics-columbia-s2018/blob/master/aics-swagger.yaml
```
Create Lambda functions (LF0, LF1, LF2) to handle chatbot logic.

### **4.Configure Lex Chatbot**
Create a Lex bot with the following intents:
- GreetingIntent
- ThankYouIntent
- DiningSuggestionsIntent
Use LF1 as the Lex code hook.
### **5. Scrape & Store Restaurant Data**
Use the Yelp API to collect 5,000+ restaurants in Manhattan.
Store data in DynamoDB (yelp-restaurants).
Store partial data (RestaurantID & Cuisine) in OpenSearch (restaurants index).
6. Process User Requests
Set up an SQS queue to receive user dining requests.
A scheduled Lambda function (LF2) processes requests and sends restaurant suggestions via SES.

### API Endpoints
| Endpoint| 	Method|	Description|
|----------|----------|----------|
| /chat   | POST   | Handles user messages and forwards them to Lex  |
| /recommendations | GET	Fetches|   restaurant recommendations from OpenSearch & DynamoDB|


### Technologies Used
- AWS Services: Lex, Lambda, API Gateway, DynamoDB, SQS, SES, OpenSearch, S3
- Backend: Python, Boto3
- Frontend: JavaScript, React (hosted on AWS S3)
- Database: NoSQL (DynamoDB)
- Search Engine: OpenSearch (AWS Elasticsearch)
APIs: Yelp API for restaurant data collection

### Example Chat Interaction
```vbnet
User: Hello
Bot: Hi there, how can I help?
User: I need restaurant suggestions.
Bot: Sure! What city are you looking to dine in?
User: Manhattan
Bot: Got it! What type of cuisine do you prefer?
User: Japanese
Bot: How many people?
User: Two
Bot: What date?
User: Today
Bot: What time?
User: 7 PM
Bot: Great! Lastly, what is your email?
User: user@example.com
Bot: Thank you! You’ll receive recommendations via email shortly.
```

### References
AWS Lex Documentation: https://docs.aws.amazon.com/lex/latest/dg/getting-started.html

AWS API Gateway Guide: https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html

DynamoDB Guide: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html

OpenSearch Guide: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/what-is.html

**lancelot**
