import json
import os
import streamlit as st
from streamlit import session_state
from openai import OpenAI
from dotenv import load_dotenv
import smtplib
import random
import string
import re
import datetime
import pandas as pd
import hashlib

st.set_page_config(
    page_title="Drug addiction therapist",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

session_state = st.session_state
if "user_index" not in st.session_state:
    st.session_state["user_index"] = 0

load_dotenv()

import random
def Drug_addiction_therapist(name, age, sex, previous_question=None, previous_answer=None):
    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

        prompt = f"""
        You are a Drug addiction therapist and you are consulting a patient named {name} aged {age} and {sex}, who is addicted drugs and exhibiting substance use disorder.

        As a therapist, your role is to guide the patient through a conversation to understand their condition better and provide appropriate medical advice. You should maintain a professional and empathetic tone throughout the interaction.

        Please ask the patient about the details of the drugs they have been consuming, how long they have been addicted, and any relevant information about their condition. Additionally, provide necessary precautions and recommendations.

        Your prompt should encourage the patient to respond, and you should wait for their reply before asking further questions.

        """

        if previous_question and previous_answer:
            prompt += "\n\nPrevious Conversation:\n\n"
            prompt += f"\n\nDoctor: {previous_question}\nPatient: {previous_answer}\n\n"

        messages = [{"role": "system", "content": prompt}]
        response = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo",
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def generate_medical_report(name, age, sex,previous_questions=None, previous_responses=None):
    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        prompt = f"Patient: {name}\n\nAge: {age}\n\n Sex: {sex}"
        if previous_questions and previous_responses:
            for question, response in zip(previous_questions, previous_responses):
                prompt += f"Doctor: {question}\nPatient: {response}\n\n"

        else:
            prompt += "Assistant: Can you provide any relevant information about your addiction?\nPatient:"
        prompt += "\n\nGenerate a detailed medical report for the drug addicted patient exhibiting substance use disorder. If the patient is recently getting addicted to drugs, suggest a detailed yoga and meditation plan, along with dietary recommendations. If the person is addicted to drugs for long, suggest appropriate lifestyle and dietary changes. Include the patient's medical and substance abuse history, symptoms, diagnosis, and treatment plan. Provide any necessary precautions and recommendations to the patient. The report should be detailed and comprehensive to ensure the patient's well-being and recovery."

        messages = [{"role": "system", "content": prompt}]

        response = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo",
        )
        return response.choices[0].message.content

    except Exception as e:
        st.error(f"Error getting marks: {e}")
        return None


def user_exists(email, json_file_path):
    # Function to check if user with the given email exists
    with open(json_file_path, "r") as file:
        users = json.load(file)
        for user in users["patients"]:
            if user["email"] == email:
                return True
    return False


def send_verification_code(email, code):
    SENDER_MAIL_ID = os.getenv("SENDER_MAIL_ID")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    RECEIVER = email
    server = smtplib.SMTP_SSL("smtp.googlemail.com", 465)
    server.login(SENDER_MAIL_ID, APP_PASSWORD)
    message = f"Subject: Your Verification Code\n\nYour verification code is: {code}"
    server.sendmail(SENDER_MAIL_ID, RECEIVER, message)
    server.quit()
    st.success("Email sent successfully!")
    return True


def generate_verification_code(length=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def signup(json_file_path="patients.json"):
    st.title("Student Signup Page")
    with st.form("signup_form"):
        st.write("Fill in the details below to create an account:")
        name = st.text_input("Name:")
        email = st.text_input("Email:")
        age = st.number_input("Age:", min_value=0, max_value=120)
        sex = st.radio("Sex:", ("Male", "Female", "Other"))
        password = st.text_input("Password:", type="password")
        confirm_password = st.text_input("Confirm Password:", type="password")
        if (
            session_state.get("verification_code") is None
            or session_state.get("verification_time") is None
            or datetime.datetime.now() - session_state.get("verification_time")
            > datetime.timedelta(minutes=5)
        ):
            verification_code = generate_verification_code()
            session_state["verification_code"] = verification_code
            session_state["verification_time"] = datetime.datetime.now()
        if st.form_submit_button("Signup"):
            if not name:
                st.error("Name field cannot be empty.")
            elif not email:
                st.error("Email field cannot be empty.")
            elif not re.match(r"^[\w\.-]+@[\w\.-]+$", email):
                st.error("Invalid email format. Please enter a valid email address.")
            elif user_exists(email, json_file_path):
                st.error(
                    "User with this email already exists. Please choose a different email."
                )
            elif not age:
                st.error("Age field cannot be empty.")
            elif not password or len(password) < 6:  # Minimum password length of 6
                st.error("Password must be at least 6 characters long.")
            elif password != confirm_password:
                st.error("Passwords do not match. Please try again.")
            else:
                verification_code = session_state["verification_code"]
                send_verification_code(email, verification_code)
                entered_code = st.text_input(
                    "Enter the verification code sent to your email:"
                )
                if entered_code == verification_code:
                    user = create_account(
                        name, email, age, sex, password, json_file_path
                    )
                    session_state["logged_in"] = True
                    session_state["user_info"] = user
                    st.success("Signup successful. You are now logged in!")
                elif len(entered_code) == 6 and entered_code != verification_code:
                    st.error("Incorrect verification code. Please try again.")


def check_login(username, password, json_file_path="evaluator.json"):
    try:
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)

        for user in data["patients"]:
            if user["email"] == username and user["password"] == password:
                session_state["logged_in"] = True
                session_state["user_info"] = user
                st.success("Login successful!")
                return user
        return None
    except Exception as e:
        st.error(f"Error checking login: {e}")
        return None


def initialize_database(json_file_path="patients.json"):
    try:
        if not os.path.exists(json_file_path):
            data = {"patients": []}
            with open(json_file_path, "w") as json_file:
                json.dump(data, json_file)
    except Exception as e:
        print(f"Error initializing database: {e}")


def create_account(name, email, age, sex, password, json_file_path="patients.json"):
    try:
        if not os.path.exists(json_file_path) or os.stat(json_file_path).st_size == 0:
            data = {"patients": []}
        else:
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)

        # Append new user data to the JSON structure
        email = email.lower()
        password = hashlib.md5(password.encode()).hexdigest()
        user_info = {
            "name": name,
            "email": email,
            "age": age,
            "sex": sex,
            "password": password,
            "report": None,
            "questions": None,
        }

        data["patients"].append(user_info)

        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        return user_info
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        st.error(f"Error creating account: {e}")
        return None


def login(json_file_path="evaluator.json"):
    st.title("Login Page")
    username = st.text_input("Email:")
    password = st.text_input("Password:", type="password")
    username = username.lower()
    password = hashlib.md5(password.encode()).hexdigest()

    login_button = st.button("Login")

    if login_button:
        user = check_login(username, password, json_file_path)
        if user is not None:
            session_state["logged_in"] = True
            session_state["user_info"] = user
        else:
            st.error("Invalid credentials. Please try again.")


def get_user_info(email, json_file_path="evaluator.json"):
    try:
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)
            for user in data["patients"]:
                if user["email"] == email:
                    return user
        return None
    except Exception as e:
        st.error(f"Error getting user information: {e}")
        return None


def render_dashboard(user_info, json_file_path="evaluator.json"):
    try:
        st.title(f"Welcome to the Dashboard, {user_info['name']}!")
        st.subheader("Student Information")
        st.write(f"Name: {user_info['name']}")
        st.write(f"Sex: {user_info['sex']}")
        st.write(f"Age: {user_info['age']}")
    except Exception as e:
        st.error(f"Error rendering dashboard: {e}")


def main(json_file_path="patients.json"):
    st.header("Welcome to the Patient's Dashboard!")
    page = st.sidebar.radio(
        "Go to",
        (
            "Signup/Login",
            "Dashboard",
            "Therapeutic assessment",
            "Diagnostic report",
        ),
        key="page",
    )

    if page == "Signup/Login":
        st.title("Signup/Login Page")
        login_or_signup = st.radio(
            "Select an option", ("Login", "Signup"), key="login_signup"
        )
        if login_or_signup == "Login":
            login(json_file_path)
        else:
            signup(json_file_path)

    elif page == "Dashboard":
        if session_state.get("logged_in"):
            render_dashboard(session_state["user_info"])
        else:
            st.warning("Please login/signup to view the dashboard.")

    elif page == "Therapeutic assessment":
        if session_state.get("logged_in"):
            user_info = session_state["user_info"]
            st.title("Therapeutic assessment")
            st.write("Chat with the health specialist to get medical advice.")
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)
                user_index = next(
                    (
                        i
                        for i, user in enumerate(data["patients"])
                        if user["email"] == session_state["user_info"]["email"]
                    ),
                    None,
                )
                if user_index is not None:
                    user_info = data["patients"][user_index]

            if "messages" not in st.session_state:
                st.session_state.messages = []

            if user_info["questions"] is None:
                previous_response = None
                previous_question = None
            else:
                previous_response = user_info["questions"][-1]["response"]
                previous_question = user_info["questions"][-1]["question"]
            if user_info["questions"] is not None and len(user_info["questions"]) > 0:
                for questions in user_info["questions"]:
                    st.chat_message("Doctor", avatar="🤖").write(questions["question"])
                    st.chat_message("Patient", avatar="👩‍🎨").write(questions["response"])
                
            question = Drug_addiction_therapist(
                user_info["name"],
                user_info["age"],
                user_info["sex"],
                previous_question,
                previous_response,
            )
            with st.chat_message("Doctor", avatar="🤖"):
                st.markdown(question)

            if prompt := st.chat_input("Enter your response here", key="response"):
                with st.chat_message("Patient", avatar="👩‍🎨"):
                    st.markdown(prompt)

                with open(json_file_path, "r+") as json_file:
                    data = json.load(json_file)
                    user_index = next(
                        (
                            i
                            for i, user in enumerate(data["patients"])
                            if user["email"] == session_state["user_info"]["email"]
                        ),
                        None,
                    )
                    if user_index is not None:
                        user_info = data["patients"][user_index]
                        if user_info["questions"] is None:
                            user_info["questions"] = []
                        user_info["questions"].append(
                            {"question": question, "response": prompt}
                        )
                        session_state["user_info"] = user_info
                        json_file.seek(0)
                        json.dump(data, json_file, indent=4)
                        json_file.truncate()
                    else:
                        st.error("User not found.")
                response = None
                st.rerun()

            if st.button("Complete the consultation and generate report"):
                report = generate_medical_report(
                    user_info["name"],
                    user_info["age"],
                    user_info["sex"],
                    [q["question"] for q in user_info["questions"]],
                    [q["response"] for q in user_info["questions"]],
                )
                with open(json_file_path, "r+") as json_file:
                    data = json.load(json_file)
                    user_index = next(
                        (
                            i
                            for i, user in enumerate(data["patients"])
                            if user["email"] == session_state["user_info"]["email"]
                        ),
                        None,
                    )
                    if user_index is not None:
                        user_info = data["patients"][user_index]
                        user_info["report"] = report
                        session_state["user_info"] = user_info
                        json_file.seek(0)
                        json.dump(data, json_file, indent=4)
                        json_file.truncate()
                    else:
                        st.error("User not found.")
                st.success("Report generated successfully!")
                

        else:
            st.warning("Please login/signup to chat.")


    elif page == "Diagnostic report":
        if session_state.get("logged_in"):
            st.title("Diagnostic report")
            user_info = session_state["user_info"]
            if user_info["report"] is not None:
                st.write(f"Report: {user_info['report']}")
            else:
                st.warning("You do not have a medical report yet.")
        else:
            st.warning("Please login/signup to meditate.")
    else:
        st.error("Invalid page selection.")


if __name__ == "__main__":

    initialize_database()
    main()
