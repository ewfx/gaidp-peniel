# Import Modules
from fastapi import FastAPI, UploadFile, File, Form
import csv
import io
import pandas as pd
import openpyxl
import pickle
from starlette.responses import Response
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import uvicorn
# import requests
from fastapi.responses import FileResponse
#import pymongo
import os
import openai
from openai import OpenAI
from docx import Document
import fitz
import json
import numpy as np
import ast
from sklearn.preprocessing import StandardScaler, LabelEncoder
from collections import defaultdict
# from dotenv import load_dotenv
# Load .env files
# load_dotenv()

os.environ["OPENAI_API_KEY"] = "API_KEY"

# Set Middleware
middleware = [ Middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])]

# Set up app
app = FastAPI(middleware=middleware, docs_url=None, redoc_url=None)
client = OpenAI()

# connect to MongoDB
# MONGODB_URI = "mongodb://localhost:27017"
# myclient = pymongo.MongoClient(MONGODB_URI)
# mydb = myclient["chat"]

def assign_risk_cluster(score):
    if score <= 33:
        return "Low Risk"
    elif score <= 66:
        return "Medium Risk"
    else:
        return "High Risk"

with open('Retail_context_setting.json', 'r') as file:
    context_setting = json.load(file)

messages = [ {"role": "system", "content": "Perform a comprehensive analysis of the provided bank regulatory dataset to ensure compliance with specified rules. The following rules uploaded as a .json have mandatory fields for sub-schedules. The key values are sub-schedules and values are array of mandatory fields for each corresponding sub-schedule. \n" + str(context_setting)} ]

@app.get('/')
def home():
    message = "what fields are important for risk scoring of a bank transaction involving US auto loan?"
    if message:
        messages.append(
            {"role": "user", "content": message},
        )
        chat = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages
        )
    reply = chat.choices[0].message.content
    print(f"ChatGPT: {reply}")
    messages.append({"role": "assistant", "content": reply})
    return {"is this homepage" : True, "This is chatgpt's reply": reply}

#### FIX THIS - CORS
@app.post('/upload-dataset')
async def upload_excel_parser(file: UploadFile = File(...)):
    file_extension = file.filename.split(".")[-1]
    home_directory = os.path.expanduser("~")
    downloads_folder = os.path.join(home_directory, "Downloads")
    file_path = f"{downloads_folder}\\Hackathon\\Saved/{file.filename}"  ### FIXED THIS Make dynamic
    with open(file_path, "wb") as f:
        f.write(file.file.read())
        print("file saved.")
    if file_extension == 'xlsx':
        # contents = file.file.read()
        # buffer = io.BytesIO(contents)
        # # print(buffer)
        df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved/{file.filename}", engine='openpyxl')
        print(df)
        # buffer.close()
        file.file.close()
        cols = df.columns
        _json = df.to_json()
        data = json.loads(_json)
        result = []
        for i in range(len(df)):
            res = {}
            for col in cols:
                res[col] = dict(data[col])[str(i)]
            result.append(res)
        # print(str(result))
        # with open("input_data.txt", 'w', encoding='unicode-escape') as f:
        #     f.write(str(result))
        
        messages.append({"role": "user", "content": "This is the dataset in json format:" + str(result) + "\n wait for rules to be provided. Just reply with 'Waiting for rules to be entered.' "},)
        chat = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"ChatGPT: {reply}")
        return({"reply" : reply})
    elif file_extension == 'xls':
        contents = file.file.read()
        buffer = io.BytesIO(contents)
        df = pd.read_excel(buffer)
        buffer.close()
        file.file.close()
        messages.append({"role": "user", "content": "This is the dataset in .csv format:" + csv + "\n wait for rules to be provided. Just reply with 'Waiting for rules to be entered.' "},)
        chat = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"ChatGPT: {reply}")
        return({"reply" : reply})
    elif file_extension == 'csv':
        contents = file.file.read()
        buffer = io.BytesIO(contents)
        df = pd.read_csv(buffer)
        buffer.close()
        file.file.close()
        messages.append({"role": "user", "content": "This is the dataset in .csv format:" + csv + "\n wait for rules to be provided. Just reply with 'Waiting for rules to be entered.' "},)
        chat = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"ChatGPT: {reply}")
        return({"reply" : reply})
    else:
        return "Please upload excel/.csv file."
    return "success"

@app.post('/upload-rules')
async def upload_rules_parser(file: UploadFile = File(None), message: str = Form(None)):
    if message:
        print("Received message:", message)
    else:
        message = ""
    if file:

        print("Received file.")
        extracted_text =""
        file_extension = file.filename.split(".")[-1]
        if file_extension == 'txt':
            extracted_text = file.file.read().decode("utf-8")
        elif file_extension == 'docx':
            doc = Document(file.file._file)
            fullText = []
            for para in doc.paragraphs:
                fullText.append(para.text)
            extracted_text = (fullText)
        elif file_extension == 'pdf':
            contents = await file.read()
            pdf_document = fitz.open(stream=contents, filetype="pdf")
            extracted_text = "\n".join([page.get_text("text") for page in pdf_document])
        else:
            extracted_text = ""
            return "Please upload .txt/.docx/.pdf file."
    else:
        extracted_text = ""
    if message != "" and extracted_text != "":
        messages.append({"role": "user", "content": "These set of rules are extracted from a regulatory dataset, apply these as well on the dataset uploaded" + extracted_text + "\n. " + message + ".\nOnly show where the rules failed and why they failed and how to remediate it in 3 bullet points."},)
        chat = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": "for all rows of data, Based on your observation, create a json file consisting of 'Transaction ID' and the additional fields based on the following rules. add a field to the dataset called 'flag'. Set flag to 0 if all the required fields exist and the values match the rules. Set flag to 1 if all required fields exist but any of the value is not in accordance with the rules. Set flag to 2 if any of the required fields are missing. Share the file in .json format as a response with no other text, Just the output dataset." + "If flag is set to 1, then add a field called 'failing rules' and populate it with all the rules that failed. Add another field called 'Remediation' and populate it with remediation steps for failing rules" + 
        "If flag is set to 2, then add a field called 'Missing Fields' and populate it with the fields that are missing values. Please recheck the data against the mentioned rules to avoid errors at all cost."},)
        chat = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        _json_ = chat.choices[0].message.content
        # print(f"ChatGPT: {reply}")
        _json_ = _json_.replace("`", '')
        _json_ = _json_.replace("json", "")
        # print(_json_)
        home_directory = os.path.expanduser("~")
        downloads_folder = os.path.join(home_directory, "Downloads")
        og_df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved\\test.xlsx", engine='openpyxl')
        # print(og_df.head())
        og_df["flag"] = np.nan
        og_df["failing rules"] = np.nan
        og_df["remediation"] = np.nan
        og_df["missing fields"] = np.nan
        # print(og_df.head())
        _json_ = ast.literal_eval(_json_)
        print(_json_)
        for i in range(len(_json_)):
            # print("\n\n\n" + _json_)
            doc = _json_[i]
            # print(type(doc))
            for k, v in doc.items():
                trans_id = doc["Transaction ID"]
                df_idx = og_df.index[og_df['Transaction ID'] == trans_id]
                if k == "flag":
                    flag = doc["flag"]
                    og_df.loc[df_idx, ["flag"]] = int(flag)
                elif k == "failing rules":
                    og_df.loc[df_idx, ["failing rules"]] = str(v)
                    # og_df.loc[og_df['Transaction ID'] == trans_id, 'failing rules'] = str(v)
                    # og_df['failing rules'] = np.where(og_df['Transaction ID'] == trans_id, str(v))
                elif k == "Remediation":
                    og_df.loc[df_idx, ["remediation"]] = str(v)
                    # og_df.loc[og_df['Transaction ID'] == trans_id, 'remediation'] = str(v)
                    # og_df['remediation'] = np.where(og_df['Transaction ID'] == trans_id, str(v))
                elif k == "Missing Fields":
                    og_df.loc[df_idx, ["missing fields"]] = str(v)
                    # og_df.loc[og_df['Transaction ID'] == trans_id, 'missing fields'] = str(v)
                    # og_df['missing fields'] = np.where(og_df['Transaction ID'] == trans_id, str(v))
            # failing_rules = doc["failing rules"]
            # rem = doc["remediation"]
            # og_df["missing fields"]
        # print(og_df.head())
        missing_fields = og_df["missing fields"]
        failing_rules = og_df["failing rules"]
        csv_buffer = io.StringIO()
        og_df.to_csv(csv_buffer, index=False)
        csv_string = csv_buffer.getvalue()
        og_df.to_excel(f"{downloads_folder}\\Hackathon\\Saved\\test.xlsx", index=False, engine='openpyxl')
        with open(os.getcwd() + "\\Models\\random_forest_model.pkl", "rb") as file:
            random_model = pickle.load(file)
        with open(os.getcwd() + "\\Models\\kmeans_model.pkl", "rb") as file:
            kmeans_model = pickle.load(file)
        zero_flag_df = og_df[(og_df['flag'] == 0)]
        zero_flag_df["Probability of Default (PD)"] = np.random.uniform(0.01, 0.20)
        zero_flag_df["Loss Given Default (LGD)"] = np.random.uniform(0.4, 0.7)
        zero_flag_df['Expected Loss (EL)'] = zero_flag_df['Probability of Default (PD)'] * zero_flag_df['Loss Given Default (LGD)'] * zero_flag_df['$ Unpaid Principal Balance at Charge-off']
        zero_flag_df["$ Unpaid Principal Balance at Charge-off"] = np.random.uniform(0.4, 0.7)
        for index, row in zero_flag_df.iterrows():
            # row["Probability of Default (PD)"] = np.random.uniform(0.01, 0.20)
            # row["Loss Given Default (LGD)"] = np.random.uniform(0.4, 0.7)
            # zero_flag_df.at[index, 'Expected Loss (EL)'] = row['Probability of Default (PD)'] * row['Loss Given Default (LGD)'] * row['$ Unpaid Principal Balance at Charge-off']
            risk_weights = {"Cash & Govt Bonds": 0.00, "Mortgages": 0.50, "Retail Loans": 0.75, "Unsecured Business Loans": 1.00,"Corporate & SME Loans": 1.50}
            loan_type = row.get("Loan Type", "Retail Loans")
            risk_weight = risk_weights.get(loan_type, 0.75)
            # row["$ Unpaid Principal Balance at Charge-off"] = row["$ Unpaid Principal Balance at Charge-off"] * risk_weight
            if row['Percent Loss Severity (3 month Lagged)'] == 0:
                zero_flag_df.at[index, 'Percent Loss Severity (3 month Lagged)'] = np.random.uniform(0.3, 0.6)
            if row["$ Net charge-offs"] == 0:
                zero_flag_df.at[index, "$ Net charge-offs"] = row["Expected Loss (EL)"] * 0.5
            if row["$ Recoveries"] == 0:
                zero_flag_df.at[index, "$ Recoveries"] = row["Loss Given Default (LGD)"] * row["$ Unpaid Principal Balance at Charge-off"]
        # Encode categorical variables
        categorical_columns = zero_flag_df.select_dtypes(include=['object']).columns
        label_encoders = {}
        for col in categorical_columns:
            le = LabelEncoder()
            zero_flag_df[col] = le.fit_transform(zero_flag_df[col])
            label_encoders[col] = le
        # Fill missing values with mean for numerical features
        zero_flag_df.fillna(zero_flag_df.mean(), inplace=True)
        features = [
            "Probability of Default (PD)", "Loss Given Default (LGD)", "Expected Loss (EL)",
            "Risk-Weighted Asset (RWA)", "$ Unpaid Principal Balance at Charge-off", "Percent Loss Severity (3 month Lagged)", "$ Net Charge-offs", "$ Recoveries"
        ]
        target = "High_Risk_Transaction_Score"
        # Scale the features
        scaler = StandardScaler()
        zero_flag_df[features] = scaler.fit_transform(zero_flag_df[features])
        X = zero_flag_df[features]
        # print(X)
        y_pred = random_model.predict(X)
        zero_flag_df_og["Risk Score"] = y_pred
        zero_flag_df_og["Risk Score"] = zero_flag_df_og["Risk Score"].astype(int)
        # print(zero_flag_df["Risk Score"])
        # zero_flag_df["Risk_Cluster"] = kmeans_model.predict(zero_flag_df[features])
        zero_flag_df_og['Risk_Label'] = zero_flag_df_og['Risk Score'].apply(assign_risk_cluster)
        # print(zero_flag_df["Risk_Label"])
        zero_flag_df_og.drop("missing fields", axis=1, inplace=True)
        zero_flag_df_og["missing fields"] = missing_fields
        zero_flag_df_og.drop("failing rules", axis=1, inplace=True)
        zero_flag_df_og["failing rules"] = failing_rules
        csv_buffer1 = io.StringIO()
        zero_flag_df_og.to_csv(csv_buffer1, index=False)
        ml_output_csv_string = csv_buffer1.getvalue()
        print(zero_flag_df_og.head())
        zero_flag_df_og.to_excel(f"{downloads_folder}\\Hackathon\\Saved\\zero_flag_test.xlsx", index=False, engine='openpyxl')
        # compliant_df = zero_flag_df[(zero_flag_df['flag'] == 0) & (zero_flag_df['Risk_Label'] == "Low Risk")]
        # reg_risk_def = og_df[(og_df['flag'] == 1)]
        # pot_def = zero_flag_df[(zero_flag_df['flag'] == 0) & (zero_flag_df['Risk_Label'] != "Low Risk")]
        # errs_df = og_df[(og_df['flag'] == 2)]
        # compliant_df_json = compliant_df.to_json(orient='records')
        # reg_risk_def_json = reg_risk_def.to_json(orient='records')
        # pot_def_json = pot_def.to_json(orient='records')
        # errs_df_json = errs_df.to_json(orient='records')
        return({"reply":reply, "df" : csv_string, "ml_out" : ml_output_csv_string})
    
    elif message == "" and extracted_text != "":
        messages.append({"role": "user", "content": "These set of rules are extracted from a regulatory dataset, apply these on the dataset uploaded" + extracted_text + ".\nOnly show where the rules failed and why they failed and how to remediate it in 3 bullet points."},)
        chat = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        # messages.append({"role": "user", "content": "Based on your observation, add a field to the dataset inputted by user called 'flag'. After your analysis, for each record add value of 'flag' as 0 if the record aligns with the inputted rules, else 1. Also add 3 more fields to the dataset 'which field'. And share back the file in .csv format as a response. No other text in response needed. Just the updated dataset with new 'flag' column along with values for each record."},)
        messages.append({"role": "user", "content": "for all rows of data, Based on your observation, create a json file consisting of 'Transaction ID' and the additional fields based on the following rules. add a field to the dataset called 'flag'. Set flag to 0 if all the required fields exist and the values match the rules. Set flag to 1 if all required fields exist but any of the value is not in accordance with the rules. Set flag to 2 if any of the required fields are missing. Share the file in .json format as a response with no other text, Just the output dataset." + "If flag is set to 1, then add a field called 'failing rules' and populate it with all the rules that failed. Add another field called 'Remediation' and populate it with remediation steps for failing rules" + 
        "If flag is set to 2, then add a field called 'Missing Fields' and populate it with the fields that are missing values. Please recheck the data against the mentioned rules to avoid errors at all cost. Errors are not expected, make sure you provide accurate data in one go."},)
        chat = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        _json_ = chat.choices[0].message.content
        # print(f"ChatGPT: {reply}")
        _json_ = _json_.replace("`", '')
        _json_ = _json_.replace("json", "")
        # print(_json_)
        home_directory = os.path.expanduser("~")
        downloads_folder = os.path.join(home_directory, "Downloads")
        og_df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved\\test.xlsx", engine='openpyxl')
        # print(og_df.head())
        og_df["flag"] = np.nan
        og_df["failing rules"] = np.nan
        og_df["remediation"] = np.nan
        og_df["missing fields"] = np.nan
        # print(og_df.head())
        print(_json_)
        _json_ = ast.literal_eval(_json_)

        for i in range(len(_json_)):
            # print("\n\n\n" + _json_)
            doc = _json_[i]
            # print(type(doc))
            for k, v in doc.items():
                trans_id = doc["Transaction ID"]
                df_idx = og_df.index[og_df['Transaction ID'] == trans_id]
                if k == "flag":
                    flag = doc["flag"]
                    og_df.loc[df_idx, ["flag"]] = int(flag)
                elif k == "failing rules":
                    og_df.loc[df_idx, ["failing rules"]] = str(v)
                    # og_df.loc[og_df['Transaction ID'] == trans_id, 'failing rules'] = str(v)
                    # og_df['failing rules'] = np.where(og_df['Transaction ID'] == trans_id, str(v))
                elif k == "Remediation":
                    og_df.loc[df_idx, ["remediation"]] = str(v)
                    # og_df.loc[og_df['Transaction ID'] == trans_id, 'remediation'] = str(v)
                    # og_df['remediation'] = np.where(og_df['Transaction ID'] == trans_id, str(v))
                elif k == "Missing Fields":
                    og_df.loc[df_idx, ["missing fields"]] = str(v)
                    # og_df.loc[og_df['Transaction ID'] == trans_id, 'missing fields'] = str(v)
                    # og_df['missing fields'] = np.where(og_df['Transaction ID'] == trans_id, str(v))
            # failing_rules = doc["failing rules"]
            # rem = doc["remediation"]
            # og_df["missing fields"]
        # print(og_df.head())
        missing_fields = og_df["missing fields"]
        failing_rules = og_df["failing rules"]
        csv_buffer = io.StringIO()
        og_df.to_csv(csv_buffer, index=False)
        csv_string = csv_buffer.getvalue()
        og_df.to_excel(f"{downloads_folder}\\Hackathon\\Saved\\test.xlsx", index=False, engine='openpyxl')
        with open(os.getcwd() + "\\Models\\random_forest_model.pkl", "rb") as file:
            random_model = pickle.load(file)
        with open(os.getcwd() + "\\Models\\kmeans_model.pkl", "rb") as file:
            kmeans_model = pickle.load(file)
        zero_flag_df = og_df[(og_df['flag'] == 0)]
        zero_flag_df_og = zero_flag_df.copy()
        zero_flag_df["Probability of Default (PD)"] = np.random.uniform(0.01, 0.20)
        zero_flag_df["Loss Given Default (LGD)"] = np.random.uniform(0.4, 0.7)
        zero_flag_df['Expected Loss (EL)'] = zero_flag_df['Probability of Default (PD)'] * zero_flag_df['Loss Given Default (LGD)'] * zero_flag_df['$ Unpaid Principal Balance at Charge-off']
        zero_flag_df["$ Unpaid Principal Balance at Charge-off"] = np.random.uniform(0.4, 0.7)
        for index, row in zero_flag_df.iterrows():
            # row["Probability of Default (PD)"] = np.random.uniform(0.01, 0.20)
            # row["Loss Given Default (LGD)"] = np.random.uniform(0.4, 0.7)
            # zero_flag_df.at[index, 'Expected Loss (EL)'] = row['Probability of Default (PD)'] * row['Loss Given Default (LGD)'] * row['$ Unpaid Principal Balance at Charge-off']
            risk_weights = {"Cash & Govt Bonds": 0.00, "Mortgages": 0.50, "Retail Loans": 0.75, "Unsecured Business Loans": 1.00,"Corporate & SME Loans": 1.50}
            loan_type = row.get("Loan Type", "Retail Loans")
            risk_weight = risk_weights.get(loan_type, 0.75)
            # row["$ Unpaid Principal Balance at Charge-off"] = row["$ Unpaid Principal Balance at Charge-off"] * risk_weight
            if row['Percent Loss Severity (3 month Lagged)'] == 0:
                zero_flag_df.at[index, 'Percent Loss Severity (3 month Lagged)'] = np.random.uniform(0.3, 0.6)
            if row["$ Net charge-offs"] == 0:
                zero_flag_df.at[index, "$ Net charge-offs"] = row["Expected Loss (EL)"] * 0.5
            if row["$ Recoveries"] == 0:
                zero_flag_df.at[index, "$ Recoveries"] = row["Loss Given Default (LGD)"] * row["$ Unpaid Principal Balance at Charge-off"]
        # Encode categorical variables
        categorical_columns = zero_flag_df.select_dtypes(include=['object']).columns
        label_encoders = {}
        for col in categorical_columns:
            le = LabelEncoder()
            zero_flag_df[col] = le.fit_transform(zero_flag_df[col])
            label_encoders[col] = le
        # Fill missing values with mean for numerical features
        zero_flag_df.fillna(zero_flag_df.mean(), inplace=True)
        features = [
            "Probability of Default (PD)", "Loss Given Default (LGD)", "Expected Loss (EL)",
            "Risk-Weighted Asset (RWA)", "$ Unpaid Principal Balance at Charge-off", "Percent Loss Severity (3 month Lagged)", "$ Net Charge-offs", "$ Recoveries"
        ]
        target = "High_Risk_Transaction_Score"
        # Scale the features
        scaler = StandardScaler()
        zero_flag_df[features] = scaler.fit_transform(zero_flag_df[features])
        X = zero_flag_df[features]
        # print(X)
        y_pred = random_model.predict(X)
        zero_flag_df_og["Risk Score"] = y_pred
        zero_flag_df_og["Risk Score"] = zero_flag_df_og["Risk Score"].astype(int)
        # print(zero_flag_df["Risk Score"])
        # zero_flag_df["Risk_Cluster"] = kmeans_model.predict(zero_flag_df[features])
        zero_flag_df_og['Risk_Label'] = zero_flag_df_og['Risk Score'].apply(assign_risk_cluster)
        zero_flag_df_og.drop("missing fields", axis=1, inplace=True)
        zero_flag_df_og["missing fields"] = missing_fields
        zero_flag_df_og.drop("failing rules", axis=1, inplace=True)
        zero_flag_df_og["failing rules"] = failing_rules
        csv_buffer1 = io.StringIO()
        zero_flag_df_og.to_csv(csv_buffer1, index=False)
        ml_output_csv_string = csv_buffer1.getvalue()
        print(zero_flag_df_og.head())
        zero_flag_df_og.to_excel(f"{downloads_folder}\\Hackathon\\Saved\\zero_flag_test.xlsx", index=False, engine='openpyxl')
        # compliant_df = zero_flag_df[(zero_flag_df['flag'] == 0) & (zero_flag_df['Risk_Label'] == "Low Risk")]
        # reg_risk_def = og_df[(og_df['flag'] == 1)]
        # pot_def = zero_flag_df[(zero_flag_df['flag'] == 0) & (zero_flag_df['Risk_Label'] != "Low Risk")]
        # errs_df = og_df[(og_df['flag'] == 2)]
        # compliant_df_json = compliant_df.to_json(orient='records')
        # reg_risk_def_json = reg_risk_def.to_json(orient='records')
        # pot_def_json = pot_def.to_json(orient='records')
        # errs_df_json = errs_df.to_json(orient='records')
        return({"reply":reply, "df" : csv_string, "ml_out" : ml_output_csv_string})
    ###### FIX THIS #######################333
    elif message != "" and extracted_text == "":
        messages.append({"role": "user", "content": message},)
        chat = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"ChatGPT: {reply}")
        return({"reply":reply})

@app.get('/pie-chart')
def pie_chart():
    # flag 0 - low
    # flag 0 - med high - potential
    # flag 1 -
    # flag 2
    home_directory = os.path.expanduser("~")
    downloads_folder = os.path.join(home_directory, "Downloads")
    zero_df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved\\zero_flag_test.xlsx", engine='openpyxl')
    og_df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved\\test.xlsx", engine='openpyxl')
    cat1 = zero_df[(zero_df['flag'] == 0) & (zero_df['Risk_Label'] == "Low Risk")]
    cat2 = zero_df[(zero_df['flag'] == 0) & (zero_df['Risk_Label'] != "Low Risk")]
    cat3 = og_df[((og_df['flag']) == 1.0)]
    cat4 = og_df[((og_df['flag']) == 2.0)]
    return {
            "cat1": len(cat1),
            "cat2": len(cat2),
            "cat3": len(cat3),
            "cat4": len(cat4)
            }

@app.get('/bar-graph')
def bar():
    dic = defaultdict(list)
    mapping = {
        'A.1 - INTERNATIONAL AUTO LOAN' : "IntAuto",
        'A.2 - US AUTO LOAN' : "Auto",
        'A.3 - INTERNATIONAL CREDIT CARD' : "IntCard",
        'A.4 - INTERNATIONAL HOME EQUITY' : "IntHE",
        'A.5 - INTERNATIONAL FIRST LIEN MORTGAGE' : "IntFM",
        'A.6 - INTERNATIONAL OTHER CONSUMER SCHEDULE' : "IntlOthCons",
        'A.7 - US OTHER CONSUMER' : "USOthCons",
        'A.8 - INTERNATIONAL SMALL BUSINESS' : "IntSB",
        'A.9 - US SMALL BUSINESS' : "USSB",
        'A.10 - STUDENT LOAN' : "Student"
    }
    schedules = ['A.1 - INTERNATIONAL AUTO LOAN', 'A.2 - US AUTO LOAN', 'A.3 - INTERNATIONAL CREDIT CARD', 'A.4 - INTERNATIONAL HOME EQUITY', 'A.5 - INTERNATIONAL FIRST LIEN MORTGAGE', 'A.6 - INTERNATIONAL OTHER CONSUMER SCHEDULE', 'A.7 - US OTHER CONSUMER', 'A.8 - INTERNATIONAL SMALL BUSINESS', 'A.9 - US SMALL BUSINESS', 'A.10 - STUDENT LOAN']

    home_directory = os.path.expanduser("~")
    downloads_folder = os.path.join(home_directory, "Downloads")
    zero_flag_df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved\\zero_flag_test.xlsx", engine='openpyxl')
    og_df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved\\test.xlsx", engine='openpyxl')
    compliant_df = zero_flag_df[(zero_flag_df['flag'] == 0) & (zero_flag_df['Risk_Label'] == "Low Risk")]
    reg_risk_def = og_df[(og_df['flag'] == 1)]
    pot_def = zero_flag_df[(zero_flag_df['flag'] == 0) & (zero_flag_df['Risk_Label'] != "Low Risk")]
    errs_df = og_df[(og_df['flag'] == 2)]
    for schedule in schedules:
        sch = mapping[schedule]
        dic[sch].append(int((compliant_df['PORTFOLIO_ID'] == sch).sum()))
        dic[sch].append(int((reg_risk_def['PORTFOLIO_ID'] == sch).sum()))
        dic[sch].append(int((pot_def['PORTFOLIO_ID'] == sch).sum()))
        dic[sch].append(int((errs_df['PORTFOLIO_ID'] == sch).sum()))
    return({
            "data" : dic
        })

@app.get('/line-graph')
def line():
    dic = defaultdict(list)
    mapping = {
        'A.1 - INTERNATIONAL AUTO LOAN' : "IntAuto",
        'A.2 - US AUTO LOAN' : "Auto",
        'A.3 - INTERNATIONAL CREDIT CARD' : "IntCard",
        'A.4 - INTERNATIONAL HOME EQUITY' : "IntHE",
        'A.5 - INTERNATIONAL FIRST LIEN MORTGAGE' : "IntFM",
        'A.6 - INTERNATIONAL OTHER CONSUMER SCHEDULE' : "IntlOthCons",
        'A.7 - US OTHER CONSUMER' : "USOthCons",
        'A.8 - INTERNATIONAL SMALL BUSINESS' : "IntSB",
        'A.9 - US SMALL BUSINESS' : "USSB",
        'A.10 - STUDENT LOAN' : "Student"
    }
    schedules = ['A.1 - INTERNATIONAL AUTO LOAN', 'A.2 - US AUTO LOAN', 'A.3 - INTERNATIONAL CREDIT CARD', 'A.4 - INTERNATIONAL HOME EQUITY', 'A.5 - INTERNATIONAL FIRST LIEN MORTGAGE', 'A.6 - INTERNATIONAL OTHER CONSUMER SCHEDULE', 'A.7 - US OTHER CONSUMER', 'A.8 - INTERNATIONAL SMALL BUSINESS', 'A.9 - US SMALL BUSINESS', 'A.10 - STUDENT LOAN']

    home_directory = os.path.expanduser("~")
    downloads_folder = os.path.join(home_directory, "Downloads")
    zero_flag_df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved\\zero_flag_test.xlsx", engine='openpyxl')
    for schedule in schedules:
        sch = mapping[schedule]
        filtered_df = zero_flag_df[(zero_flag_df['PORTFOLIO_ID'] == sch)]
        total_filtered_rows = len(filtered_df)
        sum_risk_score = int(filtered_df["Risk Score"].sum())
        # print(filtered_df.head())
        if total_filtered_rows > 0:
            avg_risk_score_for_sub_schedule = sum_risk_score//total_filtered_rows
        else:
            avg_risk_score_for_sub_schedule = 0
        dic[sch] = avg_risk_score_for_sub_schedule
    return({
            "data" : dic
        })

@app.get('/tables')
def tables():
    home_directory = os.path.expanduser("~")
    downloads_folder = os.path.join(home_directory, "Downloads")
    zero_flag_df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved\\zero_flag_test.xlsx", engine='openpyxl')
    og_df = pd.read_excel(f"{downloads_folder}\\Hackathon\\Saved\\test.xlsx", engine='openpyxl')
    compliant_df = zero_flag_df[(zero_flag_df['flag'] == 0) & (zero_flag_df['Risk_Label'] == "Low Risk")]
    reg_risk_def = og_df[(og_df['flag'] == 1)]
    pot_def = zero_flag_df[(zero_flag_df['flag'] == 0) & (zero_flag_df['Risk_Label'] != "Low Risk")]
    errs_df = og_df[(og_df['flag'] == 2)]
    compliant_df_json = compliant_df.to_json(orient='records')
    reg_risk_def_json = reg_risk_def.to_json(orient='records')
    pot_def_json = pot_def.to_json(orient='records')
    errs_df_json = errs_df.to_json(orient='records')
    return({
        "compliant_df_json":compliant_df_json, # 0
        "reg_risk_def_json":reg_risk_def_json,  # 1
        "pot_def_json":pot_def_json,  # 2
        "errs_df_json":errs_df_json # 1
        })

@app.get('/reset-session')
def reset():
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# falg = 2 -- erros in data
# flag = 0 -- risk medium high -- pot defaulters
# flag = 1 - reg risk def
# flag = 0 - risk low -- compliant 