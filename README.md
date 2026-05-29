# AI Requirements Generator (Django + OpenAI)

A Django web application that uses the OpenAI API to generate structured software requirements documents from a plain-text project description.

---

## Features

* Input a simple project description
* Generate a structured requirements document using OpenAI
* Download or copy generated output
* Django-based backend with clean API integration
* Easy to extend for different document formats (SRS, user stories, etc.)

---

## How It Works

1. User submits a project description through the web interface
2. Django backend sends the prompt to OpenAI API
3. The LLM asks a series of questions so it can get a better understanding of the project 
4. AI generates a structured requirements document from the response of the user to those questions
5. Response is formatted and returned to the user

---

## Tech Stack

* Python 3.10+
* Django
* OpenAI API
* HTML and Bootstrap 

---

